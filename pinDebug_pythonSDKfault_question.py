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

#current state of code is it outputs this when you issue LOAD"A",8 but only on first time
#MPY: soft reboot
#1 0b10100 0x28     << correct
#2 0b10000111 0xe1  << wrong should be 0xf0
#3 0b11111111 0xff  << should be filename bytes "A" in petsci
#4 0b100010 0x44    << should be 0x3f unlisten
#5 0b1010000 0xa    << should be 48 tells device 8 to talk


@asm_pio(set_init=(PIO.IN_LOW,PIO.IN_LOW,PIO.OUT_LOW),autopush=True, push_thresh=8,in_shiftdir=PIO.SHIFT_LEFT)
def myPins():
    #wait(0, gpio, 4)   # wait for ATN true    	
    wrap_target()
    
    #step 0
    set(pindirs,0b100)  # set data output, clock input, atn input
    set(pins,0b000)    [26]# set data to true
    set(pins,0b000)    [26]# set data to true
    # wait bus command wait for ATN true = 0
    
    wait(0, gpio, 2)   # wait for clock true
    #step 1
    wait(1, gpio, 2)  # wait for clock false - signals that talker ready to send
    set(pins,0b000)    [26]# set data to true
    set(pins,0b000)    [26]# set data to true
   
    set(pins,0b000)    [13]# set data to true
    #set(pins,0b00)    [26]# set data to true    
    #step 2
    set(pins,0b100)   # set data to false
    set(pindirs,0b000)  # set both pins to inputs    
    set(x,8)
    wait(0, gpio, 2)
    label("bitReadStart")
    ## read the bits   =least LSB first and true 0volts= bit set to 1, false = 5volts = bit set to 0
    wait(1, gpio, 2)   # wait for clock to go false
    in_(pins, 1)       # input one bit from GPIO 3 
    wait(0, gpio, 2)   # wait for clock to go true
    jmp(x_dec,"bitReadStart")
    
    ##DEBUG fil fifo with a progress counter - this will be read by main loop (we have autopush 8 set 
    #set(x,4)
    #in_(x, 8)
    ##    
    # step 4
    wait(0, gpio, 2)    # wait for clock true
    wrap()


sm1 = StateMachine(0, myPins, freq=10_000_000,in_base=Pin(4), set_base=Pin(2))
sm1.active(1)
#sm2 = StateMachine(0, myPins, freq=2_000_000, set_base=Pin(3))
#sm2.active(1)

while True:
    count = 0
    while True:
        count = count + 1
        rawValue = sm1.get()
        toConvert = rawValue
        inverted_bits = toConvert & 0xff
        # Convert from MSB to LSB
        msb_to_lsb = 0
        for i in range(8):
            msb_to_lsb |= ((inverted_bits >> i) & 1) << (7 - i)
        print(count, bin(rawValue), hex(msb_to_lsb))