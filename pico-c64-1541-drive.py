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
import rp2 
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

## some pins for LED to enable quick debugging
ledClock = Pin(10, Pin.OUT)
ledData = Pin(11, Pin.OUT)
ledATN = Pin(12, Pin.OUT)
ledHeartbeat = Pin(13, Pin.OUT)

#read clock PIO waits for clock rising from 0 (true) to 1 (false) then siganls IRQ
@rp2.asm_pio()
def readClockPinPIO():
    set(pins, 1)   # set base pin (clock to input)
    wrap_target()
    wait(0, pin, 0)   [31]
    wait(0, pin, 0)   [31]
    irq(block, rel(0))    
    wrap()
    
### The purpose of this PIO state machine is to handle all the low level CBM Bus activity
    
###comments are mostly from https://en.wikipedia.org/wiki/Commodore_bus
@rp2.asm_pio()
def handleCBM_BusLowLevel():
    ## Base pin 0 should be IEC_PIN_CLOCK == GPIO 2    
    wrap_target()
    set (pindirs, 0b00000010)  # Set clock 0 and atn 2 as inputs, pin 1 data is an output
   
    ## set(dest, value)
    ##wait(0, pin, 2)   # wait for ATN pin to go  IEC_TRUE = 0 (note not final solution)    
    
    # Transmission begins with the bus talker holding the Clock line true (ZERO),
    # and the listener(s) holding the Data line true. To begin the talker
    # releases the Clock line to false.
    wait(0, pin, 0)   # initially wait for clock pin TRUE=0
    set(0,0)		  # initially set data line TRUE
    
    wait(1, pin, 0)   # wait for clock pin false=1
    #When all bus listeners are ready to receive they release the Data line to false.
    set(1,1)			 # hold data line to FALSE
    
    set(pindirs, 0b00000000)      # set all pins to input    
    set(x,8)          # setup read loop count 8 bits into x
    
    wait(0, pin, 0)   # wait for clock true 0 in prep for rising edge
    
    label("bitReadLoop")  
    wait(1, pin, 0)
    in_(1, 1)         # read 1 bit from pin 1 (Data)   
    wait(0, pin, 0)   # wait for the clock pin IEC_TRUE = 0    
    jmp(x_dec, "bitReadLoop")
    
    push(block)            # push the 8 bits to the cpu    
    set(pindirs, 0b00000010)    # set data pin to output
    set(1,0)    [31]
    wrap()

basePin = Pin(IEC_PIN_CLOCK)
sm0 = rp2.StateMachine(0, handleCBM_BusLowLevel,freq=125_000_000, in_base=basePin)
# Function to read from FIFO
def read_fifo():
    while True:
        yield sm0.get()
        
def testPinsPIO():
### base pin 2 = CLOCK = 0
###      pin 3 = DATA  = 1
###      pin 4 = ATN   = 2
###      pin 5 = RESET = 3     ### not used
    sm0.active(1)    
    while True:
        for data in read_fifo():
            print("Received:", ~data & 0xff)

testPinsPIO()
