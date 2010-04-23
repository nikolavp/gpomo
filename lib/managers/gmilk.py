try:
   import dbus, dbus.glib
   gmilk_dbus_enabled = True
except:
   gmilk_dbus_enabled = False

class Gmilk:
   def __init__(self):
      self.init_server()

   def init_server(self):
      self.reset_server()
      try:
         if gmilk_dbus_enabled:
            self.bus      = dbus.SessionBus()
            self.server   = dbus.Interface(self.bus.get_object('com.Gmilk', '/'),'com.Gmilk.Interface')
            return True
      except Exception as exc:            
         print "Error initializing Gmilk Dbus client: %s %s" % (exc,self.server)
         self.reset_server()
      return False

   def reset_server(self):
      self.bus    = None
      self.server = None

   def task_count(self):
      try:
         if self.server==None:
            if not self.init_server():
               return -1
         return self.server.task_count()
      except Exception as exc:
         print "Error getting the task count on Gmilk Dbus client: %s %s" % (exc,self.server)
         self.reset_server()
         return -1

   def get_task(self,i):
      try:
         if self.server==None:
            if not self.init_server():
               return -1
         task = list(self.server.get_task(i))
         task.append(-1) # dont have any points associated
         return tuple(task)
      except Exception as exc:
         print "Error returning task from Gmilk Dbus client: %s %s" % (exc,self.server)
         self.reset_server()
         return None

   def start_task(self,id):
      pass

   def complete_task(self,id):
      try:
         if self.server==None:
            if not self.init_server():
               return -1
         return self.server.complete_task(id,True)>0
      except Exception as exc:
         print "Error completing task with id %s on Gmilk Dbus client: %s %s" % (id,exc,self.server)
         self.reset_server()
         return None
