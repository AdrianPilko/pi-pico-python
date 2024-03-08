from machine import Pin
from rp2 import PIO, StateMachine, asm_pio
import time

#rp2.asm_pio(*, out_init=None, set_init=None, sideset_init=None, in_shiftdir=0, out_shiftdir=0, autopush=False, autopull=False, push_thresh=32, pull_thresh=32, fifo_join=PIO.JOIN_NONE)¶
#Assemble a PIO program.
#The following parameters control the initial state of the GPIO pins, as one of
# PIO.IN_LOW, PIO.IN_HIGH, PIO.OUT_LOW or PIO.OUT_HIGH. If the program uses more
# than one pin, provide a tuple, e.g. out_init=(PIO.OUT_LOW, PIO.OUT_LOW).
#out_init configures the pins used for out() instructions.
#set_init configures the pins used for set() instructions. There can be at most 5.

@asm_pio(set_init=(PIO.OUT_LOW, PIO.OUT_LOW))
#set(dest, data)
#set dest with the value data.
#   dest: pins, x, y, pindirs
#   data: value (0-31)
def myPins():
    wrap_target()
    set(0,0b00)
    set(0,0b11)   
    wrap()


sm1 = StateMachine(1, myPins, freq=2_000_000, set_base=Pin(2))
sm1.active(1)
#sm2 = StateMachine(0, myPins, freq=2_000_000, set_base=Pin(3))
#sm2.active(1)

while True:
    time.sleep_ms(100)