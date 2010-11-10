#!/usr/bin/python
__appname__    = "Gpomo"
__author__     = "Eustaquio 'TaQ' Rangel"
__copyright__  = "2010 Eustaquio 'TaQ' Rangel"
__version__    = "0.0.1"
__license__    = "GPL"
__email__      = "eustaquiorangel@gmail.com"
__website__    = "http://github.com/taq/gpomo"
__date__       = "$Date: 2010/04/12 12:00:00$"

import os
import sys
import gtk
import glob
import gobject
import pygtk
import pygst
import gst
import gconf
import locale
import gettext
import datetime
import threading

from pomo_thread import *
from lock_thread import *
from configwindow import *

pygtk.require('2.0')

try:
   import pynotify
   notify = 1
except:
   notify = 0

try:
   import dbus, dbus.glib
   dbus_enabled = 1
except:
   dbus_enabled = 0

BASE_DIRS = [os.path.join(os.path.expanduser("~"), ".local", "share"),"/usr/share/pyshared","/usr/local/share", "/usr/share"]
DATA_DIRS = [os.path.abspath(sys.path[0])] + [os.path.join(d,__appname__.lower()) for d in BASE_DIRS]

gettext.bindtextdomain(__appname__.lower())
gettext.textdomain(__appname__.lower())
_ = gettext.gettext

gobject.threads_init()

class Gpomo:
   
   def __init__(self):
      self.gconf     = gconf.client_get_default()
      self.completes = 0
      self.breaks    = 0
      self.longbreaks= 0
      self.canceleds = 0
      self.canceled  = False
      self.locked    = False
      self.started   = datetime.datetime.now()
      self.task      = None
      self.task_pnt  = {}

      self.player = gst.element_factory_make("playbin2", "player")
      fakesink = gst.element_factory_make("fakesink", "fakesink")
      self.player.set_property("video-sink", fakesink)
      bus = self.player.get_bus()
      bus.add_signal_watch()

      self.timeout   = self.gconf.get_int("/apps/gpomo/timeout")
      if self.timeout<1:
         self.timeout = 25
         self.gconf.set_int("/apps/gpomo/timeout",self.timeout)

      self.interval   = self.gconf.get_int("/apps/gpomo/interval")
      if self.interval<1:
         self.interval = 5
         self.gconf.set_int("/apps/gpomo/interval",self.interval)

      self.longer   = self.gconf.get_int("/apps/gpomo/longer")
      if self.longer<1:
         self.longer = 20
         self.gconf.set_int("/apps/gpomo/longer",self.longer)

      self.connect_points = self.gconf.get_bool("/apps/gpomo/connect_points")

      self.menu = gtk.Menu()

      self.statusIcon = gtk.StatusIcon()
      self.statusIcon.set_from_file(self.get_icon("gray.png"))
      self.statusIcon.set_visible(True)
      self.statusIcon.connect('activate'  , self.left_click, self.menu)
      self.statusIcon.connect('popup-menu', self.right_click, self.menu)
      self.statusIcon.set_visible(1)

      self.configItem = gtk.MenuItem(_("Configuration"))
      self.configItem.connect('activate', self.config, self.statusIcon)
      self.menu.append(self.configItem)

      self.statItem = gtk.MenuItem(_("Statistics"))
      self.statItem.connect('activate', self.stats, self.statusIcon)
      self.menu.append(self.statItem)

      self.aboutItem = gtk.MenuItem(_("About"))
      self.aboutItem.connect('activate', self.about, self.statusIcon)
      self.menu.append(self.aboutItem)

      self.quitItem = gtk.MenuItem(_("Quit"))
      self.quitItem.connect('activate', self.quit, self.statusIcon)
      self.menu.append(self.quitItem)

      self.init_managers()
      self.default_state()
      if notify>0:
         pynotify.init("Gpomo")

      self.thread = None
      self.completed = False

      gtk.main()

   def get_managers_path(self):
      for base in DATA_DIRS:
         path = os.path.join(base,"lib","managers")
         if os.path.exists(path):
            return path
      return None         

   def init_managers(self):
      self.managers = []
      path = self.get_managers_path()
      if path==None:
         return
      sys.path.append(path)
      list = [os.path.splitext(os.path.basename(file))[0] for file in glob.glob(os.path.join(path,"*.py"))]
      for manager in list:
         mod = __import__(manager)
         cls = getattr(mod,manager.capitalize())
         self.managers.append(cls())
         self.set_tooltip(_("%s task manager loaded") % manager.capitalize())

   def set_tooltip(self,text):
      self.statusIcon.set_tooltip(text)

   def get_icon(self,icon):
      for base in DATA_DIRS:
         path = os.path.join(base,"images",icon)
         if os.path.exists(path):
            return path
      return None         

   def stats_str(self):
      return _("%(comp)d pomodoro(s) completed\n%(canceled)d pomodoro(s) canceled\n%(breaks)d breaks\n%(longbreaks)d long breaks") % {"comp":self.completes,"canceled":self.canceleds,"breaks":self.breaks,"longbreaks":self.longbreaks}

   def stats(self,widget,data):
      self.show_info(_("About this session\n\nStarted on %(start)s\n\n%(str)s") % {"start":self.started.strftime(_("%m/%d/%Y %H:%M:%S")),"str":self.stats_str()})

   def show_error(self,msg):
      self.show_dialog(gtk.MESSAGE_ERROR,msg)

   def show_info(self,msg):
      self.show_dialog(gtk.MESSAGE_INFO,msg)

   def show_dialog(self,msg_type,msg):    
      dialog = gtk.MessageDialog(None,gtk.DIALOG_MODAL,msg_type,gtk.BUTTONS_OK,msg)
      dialog.set_title(__appname__)
      dialog.run()
      dialog.destroy()

   def right_click(self, widget, button, time, data = None):
      if self.locked:
         self.show_error(_("Locked! Sorry, you can't cheat and restart this app. Go take your break."))
         return

      data.show_all()
      data.popup(None, None, gtk.status_icon_position_menu, button, time, self.statusIcon)

   def left_click(self,widget,data):
      if self.locked:
         self.show_error(_("Locked! You don't want to start another pomodoro before your break ends, right?"))
         return

      if self.completed:
         self.default_state()
         self.completed = False
         return

      if self.thread==None:
         rsp = self.ask(_("Are you sure you want to start a new pomodoro?"))
         if rsp==gtk.RESPONSE_NO:
            return
      self.start_pomodoro()

   def default_state(self):
      self.blinking(False)
      self.statusIcon.set_from_file(self.get_icon("gray.png"))
      self.set_tooltip(_("Click to start a pomodoro\n%s") % self.stats_str())

   def ask(self,msg):
      dialog = gtk.MessageDialog(None,gtk.DIALOG_MODAL,gtk.MESSAGE_QUESTION,gtk.BUTTONS_YES_NO,msg)
      rsp = dialog.run()
      dialog.destroy()
      return rsp

   def choose_task(self,tasks):
      self.task   = None
      dialog      = gtk.Dialog(_("Select a task"),None,gtk.DIALOG_MODAL,(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
      combobox    = gtk.combo_box_new_text()

      for task in tasks:
         combobox.append_text(task[2])

      dialog.vbox.pack_start(combobox)
      dialog.show_all()
      response = dialog.run()
      select   = combobox.get_active()
      dialog.destroy()

      if(response==gtk.RESPONSE_ACCEPT and select>=0):
         self.task = tasks[select]

   def start_pomodoro(self):
      if self.thread!=None:
         rsp = self.ask(_("Cancel current pomodoro?"))
         if rsp==gtk.RESPONSE_NO:
            return
         else:
            self.cancel_pomodoro()
            return

      tasks = []
      for manager in self.managers:
         count = manager.task_count()
         for i in range(0,count):
            id, name, due, points = manager.get_task(i)
            tasks.append([manager,id,name,due,points])

      if len(tasks)>0:
         response = self.ask(_("Do you want to associate your pomodoro to a task?"))
         if response==gtk.RESPONSE_YES:
            self.choose_task(tasks)
            if self.task!=None:
               manager, id, name, due, points = self.task

               if self.connect_points:
                  if points!=None and int(points)>0:
                     if id not in self.task_pnt:
                        self.task_pnt[id] = int(points)
                        rsp = manager.start_task(id)
               else:
                  rsp = manager.start_task(id)

      self.completed = False
      self.canceled  = False
      self.thread    = PomoThread(self,self.timeout)
      self.thread.start()

   def cancel_pomodoro(self):
      self.completed = False
      self.canceled  = True
      self.canceleds += 1

      if self.thread!=None:
         self.thread.stop()

      self.thread = None
      self.default_state()
      self.task   = None

   def lock(self,lock):
      if lock:
         self.locked = True
         need_a_long_break = (self.completes % 4)==0

         if need_a_long_break:
            msg = _("Pomodoro completed, 4 in a row!\nTake a %d minutes break now, you deserve it.") % self.longer
         else:
            msg = _("Pomodoro completed!\nTake a %d minutes break now.") % self.interval

         lock = LockThread(self,self.longer if need_a_long_break else self.interval)
         lock.start()

         self.statusIcon.set_from_file(self.get_icon("locked.png"))
         self.blinking(False)
         self.set_tooltip(msg)
         self.show_info(msg)
      else:
         self.locked = False
         self.default_state()

   def complete_pomodoro(self):
      self.thread = None
      if self.canceled==False:
         image    = gtk.Image()
         image.set_from_file(self.get_icon("red.png"))
         dialog   = gtk.Dialog(_("Time's up!"),None,gtk.DIALOG_MODAL,(_("Complete"),gtk.RESPONSE_OK,_("Cancel"),gtk.RESPONSE_CANCEL))
         label    = gtk.Label(_("Time's up! Now you need to tell\nif your pomodoro is complete or\nif you want to cancel it."))

         filepath = "/usr/share/sounds/gnome/default/alerts/glass.ogg"
         self.player.set_property("uri", "file://" + filepath)
         self.player.set_state(gst.STATE_PLAYING)

         dialog.vbox.pack_start(label,padding=10,expand=True,fill=True)
         dialog.vbox.pack_end(image,padding=10)
         dialog.show_all()
         resp = dialog.run()
         dialog.destroy()

         if resp==gtk.RESPONSE_CANCEL:
            self.show_error(_("Pomodoro canceled!"))
            self.cancel_pomodoro()
            return

         self.completed = True
         self.completes += 1
         if self.task!=None:
            manager, id, name, due, points = self.task
            comp = True

            if self.connect_points:
               if id in self.task_pnt:
                  points = self.task_pnt[id]
                  self.task_pnt[id] -= 1
                  if self.task_pnt[id]>0:
                     self.show_info(_("More %d pomodoro(s) till complete task") % self.task_pnt[id])
                     comp = False

            if comp:
               self.set_tooltip(_("Marking task as completed ..."))
               rsp = manager.complete_task(id)
               if not rsp:
                  self.show_error(_("Task '%s' could not be marked as complete, please mark it manually.") % name)

         self.lock(True)
      else:
         self.default_state()

      self.completed = True
      self.canceled  = False
      self.task      = None

   def blinking(self,blink):
      self.statusIcon.set_blinking(blink)

   def update_lock(self,timeout,sec):
      minutes  = timeout-(sec/60)
      seconds  = (timeout*60)-sec
      if minutes>1:
         self.set_tooltip(_("%d minute(s) to complete your break") % (minutes))
      else:
         self.set_tooltip(_("%d second(s) to complete your break") % (seconds))

   def update_time(self,sec):
      minutes  = self.timeout-(sec/60)
      seconds  = (self.timeout*60)-sec
      if minutes>1:
         self.set_tooltip(_("%d minute(s) to complete pomodoro, click to cancel") % (minutes))
      else:
         self.blinking(True)
         self.set_tooltip(_("%d second(s) to complete pomodoro") % (seconds))

      slice = (self.timeout/3.0)*60
      if sec<slice:
         self.statusIcon.set_from_file(self.get_icon("green.png"))
      elif sec<(slice*2):
         self.statusIcon.set_from_file(self.get_icon("orange.png"))
      elif sec<=(slice*2):
         self.statusIcon.set_from_file(self.get_icon("red.png"))

   def about(self,widget,data=None):
      self.about = gtk.AboutDialog()
      self.about.set_name(__appname__)
      self.about.set_program_name(__appname__)
      self.about.set_version(__version__)
      self.about.set_copyright(__copyright__)
      self.about.set_license(__license__)
      self.about.set_website(__website__)
      self.about.set_website_label(__website__)
      self.about.set_authors(["%s <%s>" % (__author__,__email__)])
      self.about.set_logo(gtk.gdk.pixbuf_new_from_file(self.get_icon("red.png")))
      self.about.run()
      self.about.destroy()

   def config(self, widget, data = None):
      dialog = ConfigWindow(self)

   def quit(self,widget,data=None):
      if self.thread!=None:
         self.thread.stop()
      gtk.main_quit()

if __name__ == "__main__":
   gpomo = Gpomo()
