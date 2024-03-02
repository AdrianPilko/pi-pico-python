from machine import Pin
import time
import select
import sys
import utime


IEC_TRUE = 0
IEC_FALSE = 1

led = Pin(13, Pin.OUT)
ledClock = Pin(10, Pin.OUT)
ledData = Pin(11, Pin.OUT)
ledATN = Pin(12, Pin.OUT)
IEC_1541_CLOCK = Pin(2,Pin.IN)
IEC_1541_DATA = Pin(3,Pin.IN)
IEC_1541_RESET = Pin(4,Pin.IN)
IEC_1541_ATN = Pin(5,Pin.IN)


def testPins():
    currentClock = IEC_1541_CLOCK.value()
    currentData = IEC_1541_DATA.value()
    currentATN = IEC_1541_ATN.value()
    currentReset = IEC_1541_RESET.value()

    oldClock = currentClock
    oldData = currentData
    oldATN = currentATN
    oldReset = currentReset

    ioContinuing = 1
    loopCount = 0

    while ioContinuing != 0:
        
        # slow down heartbeat led toggle
        if loopCount % 5000 == 0:
            led.toggle()
            
        oldClock = currentClock
        oldData = currentData
        oldATN = currentATN
        oldReset = currentReset
            
        currentClock = IEC_1541_CLOCK.value()
        currentData = IEC_1541_DATA.value()
        currentATN = IEC_1541_ATN.value()
        currentReset = IEC_1541_RESET.value()
        
        if (oldClock != currentClock):
            ledClock.value(currentClock)
        if (oldData != currentData):
            ledData.value(currentData)
        if (oldATN != currentATN):
            ledATN.value(currentATN)
        
        loopCount = loopCount + 1
        

def waitClock_TRUE():
    currentClock = IEC_1541_CLOCK.value()
    while  currentClock == IEC_FALSE:
        currentClock = IEC_1541_CLOCK.value()        
def waitClock_FALSE():
    currentClock = IEC_1541_CLOCK.value()
    while  currentClock == IEC_TRUE:
        currentClock = IEC_1541_CLOCK.value()        
def setData_TRUE():
    IEC_1541_DATA.value(IEC_TRUE)
def setData_FALSE():
    IEC_1541_DATA.value(IEC_FALSE)    
def waitATN_IEC_TRUE():
    currentATN = IEC_1541_ATN.value()
    while  currentATN == IEC_FALSE:
        currentATN = IEC_1541_ATN.value()        
def waitATN_IEC_FALSE():
    currentATN = IEC_1541_ATN.value()
    while  currentATN == IEC_TRUE:
        currentATN = IEC_1541_ATN.value()        

def readData():
    IEC_1541_CLOCK = Pin(2,Pin.IN)
    IEC_1541_DATA = Pin(3,Pin.OUT)
    
    waitClock_TRUE()
    
    setData_TRUE()
    timeBefore =  utime.ticks_us()
    waitClock_FALSE()
    timeAfter =  utime.ticks_us()
    
    if (timeAfter - timeBefore > 200):      
        IEC_1541_DATA = Pin(3,Pin.OUT)
        setData_TRUE()
        timeBefore =  utime.ticks_us()
        timeAfter = 0
        while timeAfter - timeBefore < 60:
            timeAfter =  utime.ticks_us()
        #sys.stdout.write('EOI ')        
        #sys.stdout.write(str(timeAfter - timeBefore))
        #sys.stdout.write('\n')            
        return 0x00
    
    IEC_1541_DATA = Pin(3,Pin.IN)
    
    data = 0x00;
    
    for i in range(1, 8):
        waitClock_FALSE()  
        pinVal = IEC_1541_DATA.value() & 0x01
        data = data | pinVal
        data = data << 1; 
        waitClock_TRUE()
    
    IEC_1541_DATA = Pin(3,Pin.OUT)
    setData_TRUE() ## acknowledge the 8 bits
    return data     

### MAIN routine   
##testPins()
loopCount = 0

while True:

    # slow down heartbeat led toggle
    #if loopCount % 5000 == 0:
    waitATN_IEC_TRUE()
           
    
    if (readData() & 0xff == 0x28):
        # Send the data
        sys.stdout.write('0x28\n')    
   
    led.toggle()
    waitATN_IEC_FALSE()
    #loopCount = loopCount + 1
                
    
    
 