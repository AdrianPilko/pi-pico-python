# MIT License
#Copyright 2024 Adrian Pilkington

# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the “Software”),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

### The Commodore Bus and the 1541 disk drive interfaces are documented in at
### least four sources (not all are self consistent or tell the same story!
### (unless that's just me)
### Commodore 64 Programmers's Reference Guide 1983 1st ed, INPUT/OUTPUT GUIDE page 363,4,5
### https://en.wikipedia.org/wiki/Commodore_bus
### https://files.commodore.software/reference-material/articles-and-guides/commodore-64-articles/commodore-iec-disected.pdf
### https://www.pagetable.com/?p=1135

## This micropython code is python intended to run on an RP2040, as housed in the Raspberry Pi Pico
## The ultimate aims of the project (though not sure it will ever materialise from my brain!
##     1) are to provide a fully functioning 1541 disk interface with SD card storage (additional hardware required)
##     2) provide a general commodore bus interface that can be used to allow connection
##        to the whole range of devices supported for that bus - printers, plotters etc
##     3) have it work on the excellent Pi Pico which is significantly cheaper than the other options
##     4) use to diagnose CBM 1541 disc drive
##     5) use to diagnose C64 (and other commodore) computers that support the 1541 disk drive

from machine import Pin
from rp2 import PIO, StateMachine, asm_pio
import time
import select
import sys
import utime

## The Commodore serial IEEE-488 bus (IEC Bus)is open collector active LOW - that means true == 0 - yes confusing!

IEC_TRUE = 0
IEC_FALSE = 1

IEC_PIN_CLOCK = 2
IEC_PIN_DATA = 3
IEC_PIN_ATN = 4
IEC_PIN_RESET = 5

DEBUG_PIN_CLOCK = 5
DEBUG_PIN_DATA = 6
DEBUG_PIN_ATN= 7

#read clock PIO waits for clock rising from 0 (true) to 1 (false) then siganls IRQ
@rp2.asm_pio(autopush=True, push_thresh=32,in_shiftdir=rp2.PIO.SHIFT_LEFT)
def readPinsForDebugPIO():
    set(pindirs, 0)   # set pins clock+data+atn+reset to input 
    wrap_target()
    ##in_(src, bit_count)
    wait (0,pin,0)    
    in_(pins, 32)    
    wrap()
    
### The purpose of this PIO state machine is to handle all the low level CBM Bus activity
   
## reminder of instruction args in micropython:
#wait(polarity, src, index)
#in_(src, bit_count)
#set(dest, data)
#out(dest, bit_count)
#mov(dest, src)

# autopush push_thresh mean you get 8bits at a time pushed automatically
####################### CLOCK ###### DATA ###### ATN
@rp2.asm_pio(set_init=(PIO.OUT_LOW, PIO.OUT_LOW,PIO.OUT_LOW),autopush=True, push_thresh=8)
def handleCBM_BusLowLevel():
    wrap_target()
    
    ## pin settings, these change during the runtime of the protocol     
    wait(0, gpio, 4)   # wait for ATN pin to go  IEC_TRUE = 0 (note not final solution)
    
    set(pindirs,0b00010)     # all pins input except data

    ## step 0: as listener (from IEC desected)
    set(pins,0b00000)     # set data to TRUE = 0V       
    wait(0, gpio, 2)      # wait for clock true    
        
    ##DEBUG fil fifo with a progress counter - this will be read by main loop (we have autopush 8 set 
    set(x,1)
    in_(x, 8)
    ##
    
    ## step 1: ready to recieve (from IEC desected)
    wait(1,gpio, 2)       # wait for clock line false
    set(0,0b00010)     # set data to TRUE = 0V       
    
    # step 2: get ready for data : step all pins to input (clock and data)
    set(pindirs, 0b00000)      # set all pins to input    
    wait(0, gpio, 2)   # wait for clock line to go true

    set(x,8)	# setup read loop count 8 bits into x
    label("bitReadLoop")  
    
    wait(1, gpio, 2)   # wait for clock pin to go  IEC_FALSE = 1 (rising edge)    
    in_(pins, 1)           # read 1 bit from pin 1 (Data)   
    wait(0, gpio, 2)   # wait for clock pin to go  IEC_TRUE = 0
      
    jmp(x_dec, "bitReadLoop")
        
    ##DEBUG fil fifo with a progress counter - this will be read by main loop (we have autopush 8 set 
    set(x,4)
    in_(x, 8)
    ##
    
    ### step 4 Frame handshake: after 8th bit the clock line is true and data line false
    ## talker expects acknowledge by listener setting data line true
    wait(1, gpio, 3)      # wait for data line false
    wait(0, gpio, 2)      # wait for clock line true    
    set(pindirs, 0b00010) # set data pin to output
    set(0,0b00010)     # set data pin to false to signal to talker we've received the bits
    
    ##DEBUG fil fifo with a progress counter - this will be read by main loop (we have autopush 8 set 
    set(x,5)
    in_(x, 8)
    ##    
    wrap()

     
def testPinsPIO():
### base pin 2 = CLOCK = 0
###      pin 3 = DATA  = 1
###      pin 4 = ATN   = 2
###      pin 5 = RESET = 3     ### not used (yet)
    
    IEC_CLOCK_PIN = Pin(2, Pin.IN)
    IEC_DATA_PIN = Pin(3, Pin.IN)
    IEC_ATN_PIN = Pin(4, Pin.IN)
    print("starting bus state machine")
    time.sleep_ms(100)
    
    basePinIEC = Pin(IEC_PIN_CLOCK)
    basePinDEBUG = Pin(DEBUG_PIN_CLOCK)
    sm0 = rp2.StateMachine(0, handleCBM_BusLowLevel,freq=4_000_000, in_base=2)
    
    sm0.active(1)
    count = 0
    while True:
        count = count + 1
        value = sm0.get()
        basePinDEBUG.toggle()
        print(count, hex(value))

testPinsPIO()

## set pins

#IEC_CLOCK_PIN = Pin(2, Pin.IN, Pin.PULL_UP)
#IEC_DATA_PIN = Pin(3, Pin.OUT, Pin.PULL_DOWN)
#IEC_ATN_PIN = Pin(4, Pin.IN, Pin.PULL_UP)
#count = 0
#while True:
#    IEC_DATA_PIN.value(0)
#    if(IEC_ATN_PIN.value() == 0):
#        #IEC_DATA_PIN = Pin(3, Pin.OUT, Pin.PULL_UP)
#        print (count,hex(IEC_CLOCK_PIN.value()), hex(IEC_DATA_PIN.value()))
#        #IEC_DATA_PIN = Pin(3, Pin.OUT, Pin.PULL_DOWN)        
#    count+=1
        