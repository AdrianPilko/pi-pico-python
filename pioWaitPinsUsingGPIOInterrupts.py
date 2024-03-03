from machine import Pin, PWM
from rp2 import PIO, StateMachine, asm_pio
import time



ATNinterrupt_flag=0
Datainterrupt_flag=0
Clockinterrupt_flag_R=0
Clockinterrupt_flag_F=0


IEC_ATN_PIN = Pin(5, Pin.IN, Pin.PULL_UP)
IEC_CLOCK_PIN = Pin(2, Pin.IN, Pin.PULL_UP)
IEC_DATA_PIN = Pin(3, Pin.IN, Pin.PULL_UP)

## some pins for LED to enable quick debugging
ledClock = Pin(10, Pin.OUT)
ledData = Pin(11, Pin.OUT)
ledATN = Pin(12, Pin.OUT)
ledHeartbeat = Pin(13, Pin.OUT)

def ATNcallback(IEC_ATN_PIN):
    global ATNinterrupt_flag
    ledATN.toggle()
    ATNinterrupt_flag = 1
def ClockCallbackRising(IEC_CLOCK_PIN):
    global Clockinterrupt_flag_R
    ledClock.toggle()
    Clockinterrupt_flag_R = 1
    
IEC_ATN_PIN.irq(trigger=Pin.IRQ_FALLING, handler=ATNcallback)
IEC_CLOCK_PIN.irq(trigger=Pin.IRQ_RISING, handler=ClockCallbackRising)

count = 0;
while True:
    if (Clockinterrupt_flag_R):
        if (ATNinterrupt_flag):    # atn is special - if the ATN goes active low then drop everything
            Clockinterrupt_flag_R = 0
            ATNinterrupt_flag = 0;
            IEC_DATA_PIN = Pin(3, Pin.OUT)           
            while IEC_CLOCK_PIN.value() == 0:
                pass      
            IEC_DATA_PIN = Pin(3, Pin.IN)
            data = 0x00;
            for i in range(1, 8):
                while IEC_CLOCK_PIN.value() == 0:
                    pass   
                pinVal = IEC_DATA_PIN.value() & 0x01                
                data = data | pinVal
                data = data << 1;
                
                while IEC_CLOCK_PIN.value() == 1:
                    pass
            IEC_DATA_PIN = Pin(3,Pin.OUT)
            print(data & 0xff)
            ledData.toggle()
            #if (data & 0xff == 0x28):
            #   print('0x28\n')    
   
            ledClock.toggle()        
    count = count+1
    ledHeartbeat.toggle()
    
    