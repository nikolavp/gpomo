try:
   import dbus, dbus.glib
   gmilk_dbus_enabled = True
except:
   gmilk_dbus_enabled = False

class Gmilk:
   def __init__(self):
      try:
         if gmilk_dbus_enabled:
            self.bus      = dbus.SessionBus()
            self.server   = dbus.Interface(self.bus.get_object('com.Gmilk', '/'),'com.Gmilk.Interface')
      except:            
         self.bus    = None
         self.server = None

   def task_count(self):
      if self.server==None:
         return -1
      return self.server.task_count()

   def get_task(self,i):
      if self.server==None:
         return -1
      return self.server.get_task(i)

   def complete_task(self,id):
      if self.server==None:
         return -1
      return self.server.complete_task(id)>0
