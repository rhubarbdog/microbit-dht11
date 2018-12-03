#
# dht11.py - a microbit implementation of dht11
# author - Phil Hall, copyright (c) November 2018
#
# this began life as raspberry pi code initial author
# https://github.com/szazo
#
# License - MIT

import microbit
import time

DEGREES = u'\xb0'

class DataError(Exception):
    pass

class DHT11:
    def __init__(self, pin=None):
        self._pin = pin
        self._pin2bit = self._pin2bit_id()
              
    def read(self):
        pin = self._pin
        buffer_ = bytearray(320)
        length = (len(buffer_) // 4) * 4
        for i in range(length, len(buffer_)):
            buffer_[i] = 1

        pin.write_digital(1)
        time.sleep_ms(50)
        self._block_irq()

        pin.write_digital(0)
        time.sleep_ms(20)
        
        pin.set_pull(pin.PULL_UP)
        
        if self._grab_bits(self._pin2bit, buffer_, length) != length:
            self._unblock_irq()
            raise Exception("Grab bits failed.")
        else:
            self._unblock_irq()

        #for b in buffer_:
        #    print(b, end = "")
        #print('')
        
        data = self._parse_data(buffer_)

        del buffer_
        
        if len(data) != 40:
            raise DataError("Too many or too few bits " + str(len(data)))

        bits = self._calc_bits(data)
        data = self._bits_to_bytes(bits)

        checksum = self._calc_checksum(data)
        if data[4] != checksum:
            raise DataError("Checksum invalid.")

        temp=data[2] + (data[3] / 10)
        humid=data[0] + (data[1] / 10)
        return (temp, humid)

    def _pin2bit_id(self):
        # this is a dictionary, microbit.pinX can't be a __hash__
        pin = self._pin
        if pin == microbit.pin0:
            shift = 3
        elif pin == microbit.pin1:
            shift = 2
        elif pin == microbit.pin2:
            shift = 1
        elif pin == microbit.pin3:
            shift = 4
        elif pin == microbit.pin4:
            shift = 5
        elif pin == microbit.pin6:
            shift = 12
        elif pin == microbit.pin7:
            shift = 11
        elif pin == microbit.pin8:
            shift = 18
        elif pin == microbit.pin9:
            shift = 10
        elif pin == microbit.pin10:
            shift = 6
        elif pin == microbit.pin12:
            shift = 20
        elif pin == microbit.pin13:
            shift = 23
        elif pin == microbit.pin14:
            shift = 22
        elif pin == microbit.pin15:
            shift = 21
        elif pin == microbit.pin16:
            shift = 16
        else:
            raise ValueError('function not suitable for this pin')

        return shift

    @staticmethod
    @micropython.asm_thumb
    def _block_irq():
        cpsid('i')          # disable interrupts to go really fast

    @staticmethod
    @micropython.asm_thumb
    def _unblock_irq():
        cpsie('i')          # enable interupts nolonger time critical

    # r0 - pin bit id
    # r1 - byte array
    # r2 - len byte array, must be a multiple of 4
    @staticmethod
    @micropython.asm_thumb
    def _grab_bits(r0, r1, r2):
        b(START)

        # DELAY routine
        label(DELAY)
        mov(r7, 0x2d)
        label(delay_loop)
        sub(r7, 1)
        bne(delay_loop)
        bx(lr)

        label(READ_PIN)
        mov(r3, 0x50)      # r3=0x50
        lsl(r3, r3, 16)    # r3=0x500000
        add(r3, 0x05)      # r3=0x500005
        lsl(r3, r3, 8)     # r3=0x50000500 -- this points to GPIO registers
        add(r3, 0x10)      # r3=0x50000510 -- points to read_digital bits
        ldr(r4, [r3, 0])   # move memory@r3 to r2
        mov(r3, 0x01)      # create bit mask in r3  
        lsl(r3, r0)        # select bit from r0
        and_(r4, r3)
        lsr(r4, r0)
        bx(lr)
    
        label(START)
        mov(r5, 0x00)      # r5 - byte array index 
        label(again)
        mov(r6, 0x00)      # r6 - current word
        bl(READ_PIN)
        orr(r6,  r4)       # bitwise or the pin into current word
        bl(DELAY)
        bl(READ_PIN)
        lsl(r4, r4, 8)     # move it left 1 byte
        orr(r6,  r4)       # bitwise or the pin into current word
        bl(DELAY)
        bl(READ_PIN)
        lsl(r4, r4, 16)     # move it left 2 bytes
        orr(r6,  r4)       # bitwise or the pin into current word
        bl(DELAY)
        bl(READ_PIN)
        lsl(r4, r4, 24)     # move it left 3 bytes
        orr(r6,  r4)       # bitwise or the pin into current word
        bl(DELAY)
    
        add(r1, r1, r5)   # add the index to the bytearra addres
        str(r6, [r1, 0])  # now 4 have been read store it
        sub(r1, r1, r5)   # reset the address
        add(r5, r5, 4)    # increase array index
        sub(r4, r2, r5)   # r4 - is now beig used to count bytes written
        bne(again)
    
        label(RETURN)
        mov(r0, r5)       # return number of bytes written

    def _parse_data(self, buffer_):
        # changed initial states, tyey are lost in the change over
        INIT_PULL_DOWN = 1
        INIT_PULL_UP = 2
        DATA_1_PULL_DOWN = 3
        DATA_PULL_UP = 4
        DATA_PULL_DOWN = 5

        #state = INIT_PULL_DOWN
        state = INIT_PULL_UP

        bit_lens = [] 
        length = 0 
        only = False
        
        for i in range(len(buffer_)):

            current = buffer_[i]
            length += 1

            if state == INIT_PULL_DOWN:
                if current == 0:
                    state = INIT_PULL_UP
                    continue
                else:
                    continue
            if state == INIT_PULL_UP:
                if current == 1:
                    state = DATA_1_PULL_DOWN
                    continue
                else:
                    continue
            if state == DATA_1_PULL_DOWN:
                if current == 0:
                    state = DATA_PULL_UP
                    continue
                else:
                    continue
            if state == DATA_PULL_UP:
                if current == 1:
                    length = 0
                    state = DATA_PULL_DOWN
                    continue
                else:
                    continue
            if state == DATA_PULL_DOWN:
                if current == 0:
                    bit_lens.append(length)
                    state = DATA_PULL_UP
                    continue
                else:
                    continue

        return bit_lens

    def _calc_bits(self, pull_up_lengths):

        shortest = 1000
        longest = 0

        for i in range(0, len(pull_up_lengths)):
            length = pull_up_lengths[i]
            if length < shortest:
                shortest = length
            if length > longest:
                longest = length

        halfway = shortest + (longest - shortest) / 2
        bits = bytearray(40)

        for i in range(len(pull_up_lengths)):
            bits[i] = pull_up_lengths[i] > halfway

        return bits

    def _bits_to_bytes(self, bits):
        data = []
        byte = 0

        for i in range(len(bits)):
            byte = byte << 1
            if bits[i]:
                byte = byte | 1

            if ((i + 1) % 8 == 0):
                data.append(byte)
                byte = 0

        return data

    def _calc_checksum(self, data):
        return data[0] + data[1] + data[2] + data[3] & 0xff

if __name__ == '__main__':

    sensor = DHT11(microbit.pin0)
    while True:
        try:
            t , h = sensor.read()
            print("%2.1f%sC  %2.1f%% " % (t, DEGREES, h))
        except DataError as e:
            print("Error : " + str(e))


        time.sleep(2)
