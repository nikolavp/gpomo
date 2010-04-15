import gtk
import pygtk
import gettext

_ = gettext.gettext

class ConfigWindow(gtk.Window):
   def __init__(self,manager):
      super(ConfigWindow,self).__init__()
      self.set_title(_("Gpomo configuration"))
      self.set_modal(True)
   
      self.manager      = manager
      self.gconf        = self.manager.gconf
      self.resp         = None
      table             = gtk.Table(2,2,True)

      minuteStr         = gtk.Label(_("Timeout"))
      self.minuteTxt    = gtk.Entry()
      self.minuteTxt.set_text(str(self.manager.timeout))

      intervalStr         = gtk.Label(_("Interval"))
      self.intervalTxt    = gtk.Entry()
      self.intervalTxt.set_text(str(self.manager.interval))

      longerStr         = gtk.Label(_("Longer interval"))
      self.longerTxt    = gtk.Entry()
      self.longerTxt.set_text(str(self.manager.longer))

      self.ok  = gtk.Button(_("Ok"))
      self.ok.connect("clicked",self.save)

      self.cancel = gtk.Button(_("Cancel"))
      self.cancel.connect("clicked",self.dontsave)

      table.attach(minuteStr,0,1,0,1)
      table.attach(self.minuteTxt,1,2,0,1)

      table.attach(intervalStr,0,1,1,2)
      table.attach(self.intervalTxt,1,2,1,2)

      table.attach(longerStr,0,1,2,3)
      table.attach(self.longerTxt,1,2,2,3)

      table.attach(self.ok,0,1,4,5)
      table.attach(self.cancel,1,2,4,5)
      
      self.add(table)
      self.show_all()

   def save(self,widget):
      timeout = int(self.minuteTxt.get_text())
      self.manager.gconf.set_int("/apps/gpomo/timeout",timeout)
      self.manager.timeout = timeout

      interval = int(self.intervalTxt.get_text())
      self.manager.gconf.set_int("/apps/gpomo/interval",interval)
      self.manager.interval = interval

      longer = int(self.longerTxt.get_text())
      self.manager.gconf.set_int("/apps/gpomo/longer",longer)
      self.manager.longer = longer

      self.destroy()

   def dontsave(self,widget):
      self.destroy()
