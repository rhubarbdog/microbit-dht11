<h1>DHT11 - temperature and humidity measurement</h1>

This sensor uses 1 wire for communication, the receipt of bits is written in assembler, it's the only way i could manage to receive all of the data.<br/><br/>

There is one user method `.read` this will either return a tuple of valid temperature and humidity data or raise an exception. The only exception to be trapped with a`try:` `except:` block is `DataError`. This will be for one of 2 reasons bad signal tansmission or the sensor failed to trigger.  The sensor may also raise a `ValueError` for using an unsuitable pin or a general `Exception` if the are issues with the assembler routines. These should both be considered as fatal.

There is some example code at the end of file `dht11.py` you need to run a REPL session to see the data output.