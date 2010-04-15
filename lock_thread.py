import time
import threading
import gobject

class LockThread(threading.Thread):
   def __init__(self,gui,timeout):
      super(LockThread,self).__init__()
      self.gui = gui
      self.timeout = timeout

   def run(self):
      count    = 0
      while(True):
         try:
            if count%15==0:
               gobject.idle_add(self.gui.update_lock,self.timeout,count)
            time.sleep(1)
            count += 1
            if count>=(self.timeout*60):
               break
         except:
            print "Error"
            break

      gobject.idle_add(self.gui.lock,False)
