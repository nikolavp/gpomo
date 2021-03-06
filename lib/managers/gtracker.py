import gettext
_ = gettext.gettext

try:
   import dbus, dbus.glib
   Gtracker_dbus_enabled = True
except:
   Gtracker_dbus_enabled = False

class Gtracker:
   def __init__(self):
      self.init_server()

   def init_server(self):
      self.reset_server()
      try:
         if Gtracker_dbus_enabled:
            self.bus      = dbus.SessionBus()
            self.server   = dbus.Interface(self.bus.get_object('com.Gtracker', '/'),'com.Gtracker.Interface')
            return True
      except Exception as exc:            
         print "Error initializing Gtracker Dbus client: %s %s" % (exc,self.server)
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
         return self.server.story_count()
      except Exception as exc:
         print "Error getting the task count on Gtracker Dbus client: %s %s" % (exc,self.server)
         self.reset_server()
         return -1

   def get_task(self,i):
      try:
         if self.server==None:
            if not self.init_server():
               return -1
         id, proj, name, points, task_id, task_name = self.server.get_story(i)
         id          = str(int(task_id)*-1) if len(task_name)>0 else id
         task_desc   = (" - %s %s" % (_("Task"),task_name)) if len(task_name)>0 else ""
         return [id,proj+": "+name+task_desc,None,points]
      except Exception as exc:
         print "Error returning task from Gtracker Dbus client: %s %s" % (exc,self.server)
         self.reset_server()
         return None

   def start_task(self,id):
      if int(id)>=0:
         return self.server.update_story(id,True,True)>0

   def complete_task(self,id):
      try:
         if self.server==None:
            if not self.init_server():
               return -1
         if int(id)<0:
            id = str(int(id)*-1)
            return self.server.complete_task(id,True)>0
         else:
            return self.server.update_story(id,False,True)>0
      except Exception as exc:
         print "Error completing task with id %s on Gtracker Dbus client: %s %s" % (id,exc,self.server)
         self.reset_server()
         return None
