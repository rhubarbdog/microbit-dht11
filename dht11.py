#
# dht11.py - a microbit implementation of dht11
# author - Phil Hall, copyright (c) November 2018
#
# this began life as raspberry pi code initial author
# https://github.com/szazo
#
# modifications
#
# ph01 - raise an exception and cull DHT11Result
# ph02 - decimal data
# ph03 - microbit
# ph04 - grab_bits - thumb assembly

DEBUG=True
from microbit import *
import time

class DataError(Exception):
    pass

class DHT11:

    def __init__(self, pin=None):
        self._pin = pin
        self._buff = bytearray(1024)
              
    def read(self):

        self._send_and_sleep(True,50,"ms")
        self._send_and_sleep(False,10,"ms") # this should be 20ms

        self._pin.set_pull(self._pin.PULL_UP)
              
        if self._pin == pin0:
            pin2bit = 3

        if self._grab_bits(pin2bit, self._buff, len(self._buff)) \
           != len(self._buff):
            raise DataError("Grab bits failed.")

        if DEBUG:
            for i in range(len(self._buff)):
                print(self._buff[i],end="")
            print("")
                
        pull_up = self._parse_data()

        if len(pull_up) != 40:
            raise DataError("Too many or too few bits "+\
                            str(len(pull_up)))

        bits = self._calc_bits(pull_up_lengths)
        the_bytes = self._bits_to_bytes(bits)

        checksum = self._calc_checksum(the_bytes)
        if the_bytes[4] != checksum:
            raise DataError("Checksum invalid.")

        temp=the_bytes[2] + (the_bytes[3] / 10)
        humid=the_bytes[0] + (the_bytes[1] / 10)
        return (temp, humid)

    def _send_and_sleep(self, high, sleep,units=None):
        if high:
            self._pin.write_digital(1)
        else:
            self._pin.write_digital(0)

        if not units is None:
            units=units.lower()
        if units == "us":
            time.sleep_us(sleep)
        elif units == "ms":
            time.sleep_ms(sleep)
        else:
            time.sleep(sleep)

        # r0 - pin bit id
        # r1 - byte array
        # r2 - len byte array, must be a multiple of 4
    @staticmethod
    @micropython.asm_thumb
    def _grab_bits(r0, r1, r2):
        mov(r5, 0x00)        # r5 - set it to 0 the error
        mov(r4, 0x03)        # r4 - set to 3 to check for remainder on // 4
        mov(r6, r2)          # r6 - temp value for r2
        and_(r6, r4)         # check r2 divides by 4
        bne(RETURN)          # error return 
        b(START)

        # DELAY routine
        label(DELAY)
        mov(r7, 0x13)
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

    def _parse_data(self):
        INIT_PULL_DOWN = 1
        INIT_PULL_UP = 2
        DATA_1_PULL_DOWN = 3
        DATA_PULL_UP = 4
        DATA_PULL_DOWN = 5

        state = INIT_PULL_DOWN

        bit_lens = [] 
        length = 0 

        for i in range(len(self._buff)):

            current = self._buff[i]
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
        bits = []

        for i in range(0, len(pull_up_lengths)):
            bit = False
            if pull_up_lengths[i] > halfway:
                bit = True
            bits.append(bit)

        return bits

    def _bits_to_bytes(self, bits):
        the_bytes = []
        byte = 0

        for i in range(0, len(bits)):
            byte = byte << 1
            if bits[i]:
                byte = byte | 1

            if ((i + 1) % 8 == 0):
                the_bytes.append(byte)
                byte = 0

        return the_bytes

    def _calc_checksum(self, the_bytes):
        return the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3] & 0xff

if __name__ == '__main__':
    from microbit import *

    sensor = DHT11(pin0)

    while True:
        try:
            t , h = sensor.read()
            #display.scroll("%2.1fC  %2.1f%% " % (t, h))
            print("%2.1fC  %2.1f%% " % (t, h))
        except DataError as e:
            #display.scroll("Error :"+str(e))
            print("Error :"+str(e))


        # no need to sleep display.scroll takes loads of time
        sleep(2000)
