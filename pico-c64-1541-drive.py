from machine import Pin
import rp2 
import time
import select
import sys
import utime


IEC_TRUE = 0
IEC_FALSE = 1

IEC_PIN_CLOCK = 2
IEC_PIN_DATA = 3
IEC_PIN_RESET =4
IEC_PIN_ATN = 5


led = Pin(13, Pin.OUT)
ledClock = Pin(10, Pin.OUT)
ledData = Pin(11, Pin.OUT)
ledATN = Pin(12, Pin.OUT)

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


@rp2.asm_pio()
def handleCBM_BusLowLevel():
    set(pins, 0b00001001)  # Set pin 0 and 3 as inputs
    wrap_target()    
    wait(3, pin, 0)   # wait for ATN pin to go  IEC_TRUE = 0 (note not final solution)
    irq(block, rel(0))    
    wait(0, pin, 0)   # wait for clock pin to go  IEC_TRUE = 0
    wait(0, pin, 1)   # wait for clock pin to go  IEC_FALSE = 1 rising edge
    out(pins, 1)     [31]   # output high to data pin
    set(pins, 0b00001011)      # set data pin to input
    set(x,7)          # setup read loop count 8 bits into x    
    label("bitReadLoop")
    wait(0, pin, 0)   # wait while the clock pin IEC_TRUE = 0    
    wait(0, pin, 1)   # wait for clock pin to go  IEC_FALSE = 1 rising edge
    ##pull()   locks up if this is commented in
    mov(y, osr)
    mov(isr, y)
    push()   
    jmp(x_dec, "bitReadLoop")
    irq(block, rel(0))    
    set(pindirs, 2)  [31]    # set data pin to output
    out(pins, 1)
    set(pins, 2)  [31]    # set data pin to input
    #irq(block, rel(0))    
    wrap()
    
def handler(sm):
    # Print a (wrapping) timestamp, and the state machine object.
    print(time.ticks_ms(), sm)

basePin = Pin(IEC_PIN_CLOCK)
sm0 = rp2.StateMachine(0, handleCBM_BusLowLevel, in_base=basePin)

# Function to read from FIFO
def read_fifo():
    while True:
        yield sm0.get()
        
def testPinsPIO():
### base pin 2 = CLOCK = 0
###      pin 3 = DATA  = 1
###      pin 4 = RESET = 2
###      pin 5 = ATN   = 3
    # Instantiate StateMachine(0) with base pin 2 (CLOCK)
    #basePin = Pin(IEC_PIN_CLOCK)
    #sm0 = rp2.StateMachine(0, handleCBM_BusLowLevel, in_base=basePin)
    sm0.irq(handler)
    sm0.active(1)    
    while True:
        for data in read_fifo():
            print("Received:", data)
    
    

def waitClock_TRUE():
    IEC_1541_CLOCK = Pin(IEC_PIN_CLOCK,Pin.IN)
    currentClock = IEC_1541_CLOCK.value()
    while  currentClock == IEC_FALSE:
        currentClock = IEC_1541_CLOCK.value()        
def waitClock_FALSE():
    IEC_1541_CLOCK = Pin(IEC_PIN_CLOCK,Pin.IN)
    currentClock = IEC_1541_CLOCK.value()
    while  currentClock == IEC_TRUE:
        currentClock = IEC_1541_CLOCK.value()        
def setData_TRUE():
    IEC_1541_DATA = Pin(IEC_PIN_CLOCK,Pin.OUT)
    IEC_1541_DATA.value(IEC_TRUE)
def setData_FALSE():
    IEC_1541_DATA = Pin(IEC_PIN_CLOCK,Pin.OUT)
    IEC_1541_DATA.value(IEC_FALSE)    
def waitATN_IEC_TRUE():
    IEC_1541_ATN = Pin(IEC_PIN_ATN,Pin.IN)
    currentATN = IEC_1541_ATN.value()
    while  currentATN == IEC_FALSE:
        currentATN = IEC_1541_ATN.value()        
def waitATN_IEC_FALSE():
    IEC_1541_ATN = Pin(IEC_PIN_ATN,Pin.IN)
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
#testPins()

testPinsPIO()
## if testPinsPIO() is uncommented then never gets here

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
                
    
    
 