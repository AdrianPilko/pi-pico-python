from machine import Pin
import time
import select
import sys


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


def readData():
    IEC_1541_CLOCK = Pin(2,Pin.IN)
    IEC_1541_DATA = Pin(3,Pin.OUT)
    
    waitClock_TRUE()
    setData_TRUE()
    waitClock_FALSE()
    ### need to put check here to make sure time in usec is less than 200 otherwise handle EOI 
    
    IEC_1541_DATA = Pin(3,Pin.IN)
    
    data = 0x00;
    i = 0; 
    while i < 8:
        waitClock_FALSE()  
        temp = IEC_1541_DATA.value()   
        data = temp | data
        data = data << 1; 
        waitClock_TRUE()
        i += 1
    
    IEC_1541_DATA = Pin(3,Pin.OUT)
    setData_TRUE() ## acknowledge the 8 bits
    return data     

### MAIN routine   
#testPins()
loopCount = 0

while True:

    # slow down heartbeat led toggle
    #if loopCount % 5000 == 0:
           
    data = readData()
    Str = "rx: 0x{:x}".format(data)
    # Send the data
    sys.stdout.write(Str)
    sys.stdout.write('\n');
   
    led.toggle()
    #loopCount = loopCount + 1
                
    
    
 