#https://core-electronics.com.au/guides/how-to-setup-a-raspberry-pi-pico-and-code-with-thonny/#repl
from machine import Pin
led = Pin(25, Pin.OUT)
led.toggle()