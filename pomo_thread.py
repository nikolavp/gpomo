import time
import threading
import gobject

class PomoThread(threading.Thread):
   def __init__(self,gui,timeout):
      super(PomoThread,self).__init__()
      self.gui = gui
      self.timeout = timeout
      self.running = True
      self.stopped = False

   def stop(self):
      self.running = False
      self.stopped = True

   def run(self):
      count    = 0
      while(self.running):
         try:
            if count%15==0:
               gobject.idle_add(self.gui.update_time,count)
            time.sleep(1)
            count += 1
            if count>=(self.timeout*60):
               break
         except:
            print "Error"
            break

      if not self.stopped:
         gobject.idle_add(self.gui.complete_pomodoro)
