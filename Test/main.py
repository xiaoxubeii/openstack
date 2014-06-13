'''
Created on May 8, 2014

@author: xiaoxubeii
'''

import eventlet
from eventlet import event
import threadgroup
      
def main():
    evt = event.Event()
    def callback():
        print "run"
        et = evt.wait()
        print "wait for ", et   
    
    pool = eventlet.GreenPool(10000)
    gt = pool.spawn(callback)
    # evt.send("success")
    gt.wait()
    # eventlet.sleep(0)
    
    
if __name__ == '__main__':
    main()

