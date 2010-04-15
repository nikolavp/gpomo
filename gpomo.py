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
import gobject
import pygtk
import gconf
import locale
import gettext
import threading

from pomo_thread import *
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

BASE_DIRS = [os.path.join(os.path.expanduser("~"), ".local", "share"),"/usr/local/share", "/usr/share"]
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

      self.default_state()
      if notify>0:
         pynotify.init("Gpomo")

      self.thread = None
      self.completed = False
      gtk.main()

   def set_tooltip(self,text):
      self.statusIcon.set_tooltip(text)

   def get_icon(self,icon):
      for base in DATA_DIRS:
         path = os.path.join(base,"images",icon)
         if os.path.exists(path):
            return path
      return None         

   def stats_str(self):
      return "%d pomodoro(s) completed\n%d pomodoro(s) canceled\n%d breaks\n%d long breaks" % (self.completes,self.canceleds,self.breaks,self.longbreaks)

   def stats(self,widget,data):
      self.show_info("About this session\n\n%s" % self.stats_str())

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
      data.show_all()
      data.popup(None, None, gtk.status_icon_position_menu, button, time, self.statusIcon)

   def left_click(self,widget,data):
      if self.completed:
         self.default_state()
         self.completed = False
         return

      if self.thread==None:
         dialog = gtk.MessageDialog(None,gtk.DIALOG_MODAL,gtk.MESSAGE_QUESTION,gtk.BUTTONS_YES_NO,_("Are you sure you want to start a new pomodoro?"))
         rsp = dialog.run()
         dialog.destroy()
         if rsp==gtk.RESPONSE_NO:
            return
      self.start_pomodoro()

   def default_state(self):
      self.blinking(False)
      self.statusIcon.set_from_file(self.get_icon("gray.png"))
      self.set_tooltip(_("Click to start a pomodoro\n%s") % self.stats_str())

   def start_pomodoro(self):
      if self.thread!=None:
         dialog = gtk.MessageDialog(None,gtk.DIALOG_MODAL,gtk.MESSAGE_QUESTION,gtk.BUTTONS_YES_NO,_("Cancel current pomodoro?"))
         rsp = dialog.run()
         dialog.destroy()
         if rsp==gtk.RESPONSE_NO:
            return
         else:
            self.cancel_pomodoro()
            return

      self.completed = False
      self.canceled  = False
      self.thread    = PomoThread(self,self.timeout)
      self.thread.start()

   def cancel_pomodoro(self):
      self.completed = False
      self.canceled  = True
      self.canceleds += 1
      self.thread.stop()
      self.default_state()
      self.thread = None

   def complete_pomodoro(self):
      self.thread = None
      if self.canceled==False:
         msg = _("Pomodoro completed!")
         self.statusIcon.set_from_file(self.get_icon("red.png"))
         self.blinking(True)
         self.set_tooltip(msg)
         self.show_info(msg)
         self.completed = True
         self.completes += 1
      else:
         self.default_state()

      self.completed = True
      self.canceled  = False

   def blinking(self,blink):
      self.statusIcon.set_blinking(blink)

   def update_time(self,sec):
      self.set_tooltip(_("%d minute(s) to complete pomodoro, click to cancel") % (self.timeout-(sec/60)))
      slice = (self.timeout/3.0)*60
      if sec<slice:
         self.statusIcon.set_from_file(self.get_icon("green.png"))
      elif sec<(slice*2):
         self.statusIcon.set_from_file(self.get_icon("orange.png"))
      elif sec<=(slice*2):
         self.statusIcon.set_from_file(self.get_icon("red.png"))

      if sec>=(slice*2)+(slice/2) and not self.statusIcon.get_blinking():
           self.statusIcon.set_blinking(True)
           self.set_tooltip(_("Few seconds to complete pomodoro"))

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
