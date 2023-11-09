# example from https://blues.io/blog/raspberry-pi-pico-pio/

import time
import rp2
from machine import Pin
@rp2.asm_pio(set_init=(rp2.PIO.OUT_LOW, rp2.PIO.OUT_HIGH, rp2.PIO.OUT_LOW))
def blink():
    wrap_target()
    set(pins, 0b100)   [31]
    nop()          [31]
    nop()          [31]
    nop()          [31]
    nop()          [31]    
    set(pins, 0b010)   [31]
    nop()          [31]
    nop()          [31]
    nop()          [31]
    nop()          [31]
    set(pins, 0b001)   [31]
    nop()          [31]
    nop()          [31]
    nop()          [31]
    nop()          [31]
    set(pins, 0b010)[31]
    nop()          [31]
    nop()          [31]
    nop()          [31]
    nop()          [31]          
    wrap()
    
sm = rp2.StateMachine(0, blink, freq=2000, set_base=Pin(26))
sm.active(1)

buttonOn = Pin(22, Pin.IN, pull=Pin.PULL_UP)
buttonOff = Pin(21, Pin.IN, pull=Pin.PULL_UP)

def handleButtonOn(pin):
    sm.active(0)

def handleButtonOff(pin):
    sm.active(1)
        
buttonOn.irq(trigger=Pin.IRQ_RISING,handler=handleButtonOn)
buttonOff.irq(trigger=Pin.IRQ_RISING,handler=handleButtonOff)

while 1 == 1:
    time.sleep(10)        
    
