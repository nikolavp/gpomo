import time
import threading
import gobject

class PomoThread(threading.Thread):
   def __init__(self,gui):
      super(PomoThread,self).__init__()
      self.gui = gui
      self.running = True

   def stop(self):
      self.running = False

   def run(self):
      timeout  = self.gui.timeout
      count    = 0
      while(self.running):
         try:
            if count%15==0:
               gobject.idle_add(self.gui.update_time,count)
            time.sleep(1)
            count += 1
            if count>=(self.gui.timeout*60):
               break
         except:
            print "Error"
            break
      gobject.idle_add(self.gui.complete_pomodoro)
