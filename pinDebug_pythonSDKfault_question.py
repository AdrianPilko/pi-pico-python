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

@asm_pio(set_init=(PIO.IN_LOW, PIO.OUT_HIGH, PIO.OUT_LOW),autopush=True, push_thresh=8,in_shiftdir=PIO.SHIFT_LEFT)
#set(dest, data)
#set dest with the value data.
#   dest: pins, x, y, pindirs
#   data: value (0-31)
def myPins():
    
    # step 0 for bus command wait for ATN true = 0
    set(pindirs,0b010)  # set data output, clock input, atn input
    wait(0, gpio, 2)   # wait for ATN true
    wrap_target()     
    #step 0
    set(0,0b00)  [31]  # set data to true
    set(0,0b00)  [31]  # set data to true
    wait(0, gpio, 2)   # wait for clock true
    #step 1
    wait(1, gpio, 2)  [31] # wait for clock false - signals that talker ready to send
    #step 2
    set(0,0b10)  [31]  # set data to false
    set(0,0b10)  [31]  # set data to false
    set(pindirs,0b100)  # set both pins to inputs
    set(x,8)   
    wait(0, gpio, 2)   # wait for clock true

    label("bitReadStart")
    ## read the bits   =least LSB first and true 0volts= bit set to 1, false = 5volts = bit set to 0
    wait(1, pin, 0)   # wait for clock to go false
    in_(pins, 1)       # input one bit from GPIO 2   
    wait(0, pin, 0)   # wait for clock to go true
    jmp(x_dec,"bitReadStart")

    # step 4
    wait(0, gpio, 2)    # wait for clock true
    set(pindirs,0b010)  # set data pin to output     
    set(0,0b00)  [31]         # set data pin to true
    set(0,0b00)  [31]         # set data pin to true    
    wrap()


sm1 = StateMachine(0, myPins, freq=8_000_000,in_base=Pin(2), set_base=Pin(2))
sm1.active(1)
#sm2 = StateMachine(0, myPins, freq=2_000_000, set_base=Pin(3))
#sm2.active(1)

while True:
    count = 0
    while True:
        count = count + 1
        value = sm1.get()
        value = ~value;
        print(count, hex(value))