import utime
from rp2 import PIO 
from machine import Pin

PIO0_BASE = const(0x50200000)
PIO1_BASE = const(0x50300000)

# register indices into the array of 32 bit registers
PIO_CTRL = const(0)
PIO_FSTAT = const(1)
PIO_FLEVEL = const(3)
SM_REG_BASE = const(0x32)  # start of the SM state tables
# register offsets into the per-SM state table
SMx_CLKDIV = const(0)
SMx_EXECCTRL = const(1)
SMx_SHIFTCTRL = const(2)
SMx_ADDR = const(3)
SMx_INSTR = const(4)
SMx_PINCTRL = const(5)

SMx_SIZE = const(6)  # SM state table size

SM_FIFO_RXFULL  = const(0x00000001)
SM_FIFO_RXEMPTY = const(0x00000100)
SM_FIFO_TXFULL  = const(0x00010000)
SM_FIFO_TXEMPTY = const(0x01000000)

@rp2.asm_pio(set_init=(rp2.PIO.IN_LOW,rp2.PIO.IN_LOW, rp2.PIO.IN_LOW), autopush=True,push_thresh=8, in_shiftdir=rp2.PIO.SHIFT_LEFT)
def IEC_CBM_Bus2():
    ## reminder of instruction args in micropython:
    #wait(polarity, src, index)
    #in_(src, bit_count)
    #set(dest, data)
    ## setting pindirs = decimal 2 = binary 10 = base+1 = data = output, clock = 0 = input
    ## setting pindirs = decimal 0 = binary 0 = base+1 = data = input, clock = 0 = input
    
    ### next line commented out for now just deal with clock and data
#    wait(0, pins, 2) ## wait for ATN to go low (true) but only on bus command
    set(pindirs, 0b10)   # clock input - data output
    
    wrap_target()  
    set(1,0)        [31] # when ready to receive the listener sets data pin to TRUE "I'm here"
    #########
    ## initial state before the instigation of any data transfer
    #########
    
    wait(1, pin, 0)   # wait for clock pin FALSE=1 (on pin 0) set by talker
    set(1,1)          [31]# when ready to receive the listener sets data pin to FALSE = 1
        
    set(pindirs, 0)  # set both clock and data to input
      
    set(x,8)             # set bit loop max to 8bits    
    label("bitReadLoop")    
    wait(1, pin, 0)   # wait for clock to go high
    in_(1, 1)           # read 1 bit from pin 1 (Data)
    wait(0, pin, 0)   # wait for clock true 0 in prep for rising edge
    jmp(x_dec, "bitReadLoop")
    
    set(pindirs, 0b10)   # clock input - data output
    set(1,0)   [31]            # hold data line false

    wrap()
 
#@rp2.asm_pio(set_init=(rp2.PIO.OUT_LOW,rp2.PIO.OUT_HIGH), autopush=True,push_thresh=8, in_shiftdir=rp2.PIO.SHIFT_LEFT)
#@rp2.asm_pio(set_init=(rp2.PIO.OUT_LOW,rp2.PIO.OUT_LOW), out_init=(rp2.PIO.OUT_LOW,rp2.PIO.OUT_LOW), autopush=True,push_thresh=8, in_shiftdir=rp2.PIO.SHIFT_LEFT)
@rp2.asm_pio(set_init=(rp2.PIO.OUT_LOW,rp2.PIO.OUT_LOW))  
def IEC_CBM_Bus():
    ## reminder of instruction args in micropython:
    #wait(polarity, src, index)
    #in_(src, bit_count)
    #set(dest, data)
    #out(dest, bit_count)
    #mov(dest, src)
    
    
    set(pindirs,0b11)
    wrap_target()
    
    ## does not work for any output other than the base pin
    set(1,0)        [10] # when ready to receive the listener sets data pin to TRUE "I'm here"
    set(1,1)        [10] # when ready to receive the listener sets data pin to TRUE "I'm here"
    set(0,0)        [3] # when ready to receive the listener sets data pin to TRUE "I'm here"
    set(0,1)        [3] # when ready to receive the listener sets data pin to TRUE "I'm here"    
    wrap()
      
    
class IEC1541Pio():
    #def __init__(self, clockGPIO, DataGPIO, ATN_GPIO, instance):
    def __init__(self, instance, clockGPIO, DataGPIO, ATN_GPIO):
        # running on the 2nd pio block which is state machine 4-7, instance count allows multiple
        # fails 1 self.sm = rp2.StateMachine(instance, IEC_CBM_Bus, freq=2000000,set_base=Pin(clockGPIO))
        # fails 2 self.sm = rp2.StateMachine(instance, IEC_CBM_Bus, freq=2000000,set_base=Pin(DataGPIO))
        # OK self.sm = rp2.StateMachine(instance, IEC_CBM_Bus, freq=2000000,set_base=Pin(DataGPIO))
        self.sm = rp2.StateMachine(instance, IEC_CBM_Bus, freq=2000000,set_base=Pin(clockGPIO))        
        
        self.sm.active(1)
        self.tx_Data = 0x00
        self.rx_Data = 0x00
        self.count = 1
        
    def getData(self):        
        self.rx_Data = self.sm.get()
        print(self.count)
        self.count = self.count + 1
        return self.rx_Data
            
StateMachineId = 1
iec_bus = IEC1541Pio(StateMachineId,2,3,4)
#myObj = PIOSPI(0)
smx0 = PIO0_BASE + 0xd8   #d4=0 ec=1   d8,f0 = instr

while True:    
    #print(hex(iec_bus.getData()))
    x = 1
    