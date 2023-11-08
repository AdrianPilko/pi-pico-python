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
    wrap()
sm = rp2.StateMachine(0, blink, freq=2000, set_base=Pin(26))
sm.active(1)
button = Pin(22, Pin.IN)

while 1 == 1:
    if button.value() == 1:
        sm.active(0)
        time.sleep(3)
        sm.active(1)
        
    
