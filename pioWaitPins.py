from machine import Pin, PWM
from rp2 import PIO, StateMachine, asm_pio
import time

@rp2.asm_pio(set_init=rp2.PIO.IN_LOW, autopush=True, push_thresh=1)
def readATN_High_Low():
    wrap_target()
    #wait(polarity, src, index)
    #in_(src, bit_count)
    wait(1, pin, 0)
    wait(0, pin, 0)    
    in_(0,1)
    wrap()

@rp2.asm_pio(set_init=rp2.PIO.IN_LOW, autopush=True, push_thresh=1)
def readCLOCK_Low_HIGH():
    wrap_target()
    #wait(polarity, src, index)
    #in_(src, bit_count)
    wait(0, pin, 0)
    wait(1, pin, 0)    
    in_(0,1)
    wrap()

@rp2.asm_pio(autopush=True, push_thresh=1)
def readDATA():
    wrap_target()
    #wait(polarity, src, index)
    #in_(src, bit_count) 
    in_(0,1)
    wrap()

IEC_CLOCK_PIN = Pin(2, Pin.IN, Pin.PULL_UP)
IEC_DATA_PIN = Pin(3, Pin.IN, Pin.PULL_UP)
IEC_ATN_PIN = Pin(4, Pin.IN, Pin.PULL_UP)

sm0 = rp2.StateMachine(0, readCLOCK_Low_HIGH,freq=125_000_000, in_base=IEC_CLOCK_PIN)
sm1= rp2.StateMachine(1, readDATA,freq=125_000_000, in_base=IEC_DATA_PIN)
sm2 = rp2.StateMachine(2, readATN_High_Low,freq=125_000_000, in_base=IEC_ATN_PIN)

sm0.active(1)
sm1.active(1)
sm2.active(1)

## some pins for LED to enable quick debugging
ledClock = Pin(5, Pin.OUT)
ledData = Pin(6, Pin.OUT)
ledATN = Pin(7, Pin.OUT)
ledHeartbeat = Pin(8, Pin.OUT)

count = 0;
while True:
    theclock = sm0.get()
    thedata = sm1.get()
    theatn = sm2.get()
    print("ATN ",count, " atn", hex(theatn), " clock=",hex(theclock), " data=",hex(thedata))
    count = count+1
    ledHeartbeat.toggle()
    