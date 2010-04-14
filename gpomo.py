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

class Gpomo:
   
   def __init__(self):
      self.gconf     = gconf.client_get_default()
      self.timeout   = self.gconf.get_int("/apps/gpomo/timeout")
      if self.timeout<1:
         self.timeout = 25
         self.gconf.set_int("/apps/gpomo/timeout",self.timeout)

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

      self.aboutItem = gtk.MenuItem(_("About"))
      self.aboutItem.connect('activate', self.about, self.statusIcon)
      self.menu.append(self.aboutItem)

      self.quitItem = gtk.MenuItem(_("Quit"))
      self.quitItem.connect('activate', self.quit, self.statusIcon)
      self.menu.append(self.quitItem)

      self.set_tooltip(_("Gpomo - Control your pomodoros"))
      if notify>0:
         pynotify.init("Gpomo")

      gtk.main()

   def set_tooltip(self,text):
      self.statusIcon.set_tooltip(text)

   def get_icon(self,icon):
      for base in DATA_DIRS:
         path = os.path.join(base,"images",icon)
         if os.path.exists(path):
            return path
      return None         

   def right_click(self, widget, button, time, data = None):
      data.show_all()
      data.popup(None, None, gtk.status_icon_position_menu, button, time, self.statusIcon)

   def left_click(self,widget,data):
      dialog = gtk.MessageDialog(None,gtk.DIALOG_MODAL,gtk.MESSAGE_QUESTION,gtk.BUTTONS_YES_NO,_("Are you sure you want to start a new pomodoro?"))
      rsp = dialog.run()
      dialog.destroy()
      if rsp==gtk.RESPONSE_NO:
         return

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
      self.about.run()
      self.about.destroy()

   def config(self, widget, data = None):
      minuteStr   = gtk.Label(_("Timeout"))
      minuteTxt   = gtk.Entry()
      minuteTxt.set_text(str(self.timeout))

      dialog      = gtk.Dialog(_("Configuration"),None,gtk.DIALOG_MODAL,(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
      dialog.vbox.pack_start(minuteStr)
      dialog.vbox.pack_start(minuteTxt)

      minuteStr.show()
      minuteTxt.show()
      response    = dialog.run()
      dialog.destroy()

      if response==gtk.RESPONSE_REJECT:
         return

      self.timeout = int(minuteTxt.get_text())
      self.gconf.set_int("/apps/gpomo/timeout",self.timeout)

   def quit(self,widget,data=None):
      gtk.main_quit()

if __name__ == "__main__":
   gpomo = Gpomo()
