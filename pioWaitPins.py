from machine import Pin, PWM
from rp2 import PIO, StateMachine, asm_pio
import time

@rp2.asm_pio(set_init=rp2.PIO.IN_LOW, autopush=True, push_thresh=32)
def atn():
    wrap_target()
    set(x, 0)
    wait(0, pin, 0)  # Wait for pin to go low
    wait(1, pin, 0)  # Low to high transition
    #label('low_high')
    #jmp(pin, 'low_high')  # while pin is low
    in_(x, 32)  # Auto push: SM stalls if FIFO full
    wrap()
@rp2.asm_pio(set_init=rp2.PIO.IN_LOW, autopush=True, push_thresh=32)
def clock():
    wrap_target()
    set(x, 0)
    wait(1, pin, 0)  # Wait for pin to go low (TRUE)
    wait(0, pin, 0)  # Low to high transition (TRUE TO FALSE)
    #label('low_high')
    #jmp(pin, 'low_high')  # while pin is high
    in_(x, 32)  # Auto push: SM stalls if FIFO full
    wrap()



IEC_ATN_PIN = Pin(5, Pin.IN, Pin.PULL_UP)
sm0 = rp2.StateMachine(0, atn,freq=500000, in_base=IEC_ATN_PIN)
sm0.active(1)
IEC_CLOCK_PIN = Pin(2, Pin.IN, Pin.PULL_UP)
sm1 = rp2.StateMachine(0, clock,freq=500000, in_base=IEC_CLOCK_PIN)
sm1.active(1)

## some pins for LED to enable quick debugging
ledClock = Pin(10, Pin.OUT)
ledData = Pin(11, Pin.OUT)
ledATN = Pin(12, Pin.OUT)
ledHeartbeat = Pin(13, Pin.OUT)

# Clock is 125MHz. 3 cycles per iteration, so unit is 24.0ns
def scale(v):
    return (1 + (v ^ 0xffffffff)) * 0.000000006  # Scale to microseconds

count = 0;
while True:
    theatn = scale(sm0.get())
    theclock = scale(sm1.get())
    print("ATN ",count, " atn", theatn, " clock=",theclock)
    count = count+1
    ledATN.toggle()
    time.sleep(0.2)
    