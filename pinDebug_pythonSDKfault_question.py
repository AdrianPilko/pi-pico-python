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
# Device	Send filename bytes <<<< never see this???!
# /3F	Devices	Unlisten all devices
# /48	Device	Talk, Device number 8
# /60	Device	Reopen channel 0
# Device number 8 becomes the master of the bus
# Host	Receive byte data
# The host becomes the master of the bus (normal operation)
# /5F	Devices	Untalk all devices
# /28	Device	Listen, device number 8
# /E0	Device	Close channel 0
# /3F	Devices	Unlisten all devices


## current output
# 2 0x28
# Listen, device number 8
# 4 0xf0
# Open channel 0
# 6 0x3f
# unlisten all devices
# 8 0x48
# talk device 8
# 10 0x60
# Reopen channel 0

@asm_pio(set_init=(PIO.IN_LOW,PIO.IN_LOW,PIO.OUT_LOW),autopush=True, push_thresh=8,in_shiftdir=PIO.SHIFT_LEFT)
def listener():
    #wait(0, gpio, 4)   # wait for ATN true    	
    wrap_target()
    
    #step 0
    set(pindirs,0b100)  # set data output, clock input, atn input
    set(pins,0b000)    [26]# set data to true
    # wait bus command wait for ATN true = 0
    
    wait(0, gpio, 2)   # wait for clock true
    #step 1    
    wait(1, gpio, 2)  # wait for clock false - signals that talker ready to send
    set(pins,0b000)    [26] # set data to true
    #step 2
    set(pins,0b100)   [26] # set data to false
    set(pindirs,0b000)  # set both pins to inputs
    wait(0, gpio, 2)
    
    in_(null,8) ## this apopears to flush the RX FIFO ?? and get the correct values
    set(x,8)    
    label("bitReadStart")
    ## read the bits   =least LSB first and true 0volts= bit set to 1, false = 5volts = bit set to 0
    wait(1, gpio, 2)   # wait for clock to go false
    in_(pins, 1)       # input one bit from GPIO 3 
    wait(0, gpio, 2)   # wait for clock to go true  
    jmp(x_dec,"bitReadStart")
    #push()  no need autopush=True
    
    # step 4
    wait(0, gpio, 2)    # wait for clock true
    wrap()

@asm_pio(set_init=(PIO.OUT_HIGH,PIO.IN_LOW,PIO.OUT_HIGH),in_shiftdir=PIO.SHIFT_LEFT)
def talker():
    #wait(0, gpio, 4)   # wait for ATN true    	
    wrap_target()
    
    #step 0
    set(pindirs,0b001)  # clock output and data input
    set(pins,0b001)    [31]# set clock to high
    # set clock to low for minimum of 80usec is a loop of 3.1usec * 25.806, at 10MHz clock freq
    ## values as per c64 programmers reference manual
    set(x,26)
    label("T_DA_delayLoop")
    set(pins,0b000)    [31]
    jmp(x_dec, "T_DA_delayLoop")
    
        
    wait(1, gpio, 4)   # wait for data high - signals the listener (c64 in this case) is now ready for data
    
    
    set(pindirs,0b101)    [26] # set clock and data to output
    pull(block) 
    set(x,8)    
    label("bitSendStart")
    
    
    set(y,10)
    label("TS_DelayLoop")
    set(pins, 0b000)   [20] # bit setup time 20usec thats 20cycles * 10iterations at 10MHz
    jmp(y_dec,"TS_DelayLoop")
    
    out(pins, 1)       # set the bit
    set(y,10)
    label("TV_DelayLoop") ## data valid holds"
    set(pins, 0b001)   [20] # transition clock and hold for 20usec thats 20cycles * 10iterations at 10MHz
    jmp(y_dec,"TV_DelayLoop");
    
    jmp(x_dec,"bitSendStart")
    
    # step 4
    set(pins, 0b000) [25]
    set(pindirs,0b100)
    wait(0, gpio, 4) 
    wrap()

sm1 = StateMachine(0, listener, freq=10_000_000,in_base=Pin(4), set_base=Pin(2))
sm2 = StateMachine(7, talker, freq=10_000_000,out_base=Pin(4), set_base=Pin(2))
sm1.active(1)
print('set stae machine 1 active - listen')

while True:
    count = 0
    while True:
        count = count + 1
        rawValue = sm1.get()
        if (rawValue & 0xff != 0):
            toConvert = rawValue
            inverted_bits = toConvert & 0xff
            # Convert from MSB to LSB
            msb_to_lsb = 0
            for i in range(8):
                msb_to_lsb |= ((inverted_bits >> i) & 1) << (7 - i)
            if msb_to_lsb==0x28:
                print('0x28 Listen, device number 8')
            elif msb_to_lsb==0xf0:
                print('0xf0 Open channel 0')            
            elif msb_to_lsb==0x3f:
                print('0x3f unlisten all devices')
            elif msb_to_lsb==0x48:
                print('0x48 talk device 8')
                sm1.active(0) 
                sm2.active(1)
                time.sleep(1)
                print('send filename \'A\'')
                time.sleep(0.1)
                sm2.put('A')
                print('sent \'A\'')
                time.sleep(0.1)
                sm2.put(0x5f)
                print('sent 0x5f')
                time.sleep(0.1)
                sm2.active(0)
                time.sleep(0.1)
                sm1.active(1)                
                print('sm2 talker state machine now inactive, listener now active')
            elif msb_to_lsb==0x60:
                print('0x60 Reopen channel 0')
            elif msb_to_lsb==0x5f:
                print('0x5f Untalk all devices')
                sm2.active(0)
                sm1.active(1)                
            elif msb_to_lsb==0xe0:
                print('0xe0 Close channel 0')
            else:
                print('got bytes ' , hex(msb_to_lsb))
                