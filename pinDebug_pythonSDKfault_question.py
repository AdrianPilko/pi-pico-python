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

#current state of code is it outputs this when you issue LOAD"A",8

## correct sequence is:
# /28	Device	Listen, device number 8
# /F0	Device	Open channel 0
# Device	Send filename bytes
# /3F	Devices	Unlisten all devices
# /48	Device	Talk, Device number 8
# /60	Device	Reopen channel 0

# MPY: soft reboot
# 1 0xaa 0b10101010 0x55
# 2 0x14 0b10100 0x28
# 3 0x1aa 0b110101010 0x55
# 4 0xf 0b1111 0xf0
# 5 0x1aa 0b110101010 0x55
# 6 0xfc 0b11111100 0x3f
# 7 0x1aa 0b110101010 0x55
# 8 0x12 0b10010 0x48
# 9 0x1aa 0b110101010 0x55
# 10 0x6 0b110 0x60

@asm_pio(set_init=(PIO.IN_LOW,PIO.IN_LOW,PIO.OUT_LOW),autopush=True, push_thresh=8,in_shiftdir=PIO.SHIFT_LEFT)
#@asm_pio(set_init=(PIO.IN_LOW,PIO.IN_LOW,PIO.OUT_LOW),push_thresh=8,in_shiftdir=PIO.SHIFT_LEFT)
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
    ##DEBUG fil fifo with a progress counter - this will be read by main loop (we have autopush 8 set 
    set(y,0b1010)
    in_(y, 4)
    in_(y, 4) 
    #push()
    ##
      
    wait(1, gpio, 2)  # wait for clock false - signals that talker ready to send
    set(pins,0b000)    [26]# set data to true
    set(pins,0b000)    [26]# set data to true
   
    set(pins,0b000)    [13]# set data to true
    #set(pins,0b00)    [26]# set data to true    
    #step 2
    set(pins,0b100)   [26] # set data to false
    set(pindirs,0b000)  # set both pins to inputs
    wait(0, gpio, 2)
    
    set(x,8)    
    label("bitReadStart")
    ## read the bits   =least LSB first and true 0volts= bit set to 1, false = 5volts = bit set to 0
    wait(1, gpio, 2)   # wait for clock to go false
    in_(pins, 1)       # input one bit from GPIO 3 
    wait(0, gpio, 2)   # wait for clock to go true
    
    jmp(x_dec,"bitReadStart")
    #push()
    
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
        print(count, hex(rawValue), bin(rawValue), hex(msb_to_lsb))