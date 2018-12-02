<h1>DHT11 - temperature and humidity measurement</h1>

This sensor uses 1 wire for communication, the receipt of bits is written in assembler, it's the only way i could manage to receive all of the data.<br/><br/>

There is one user method `.read` this will either return a tuple of valid temperature and humidity data or raise an exception. The only exception to be trapped with a `try:` `except:` block is `DataError`.  The sensor may also raise a `ValueError` for using an unsuitable pin or a general `Exception` if the are issues with the assembler routines.<br/><br/>

There is some example code at the end of file `dht11.py` you need to run a REPL session to see the data output.<br/><br/>

The sensor is wired as following :
<table>
<tr><td><center>Pin</center></td></tr>
<tr><td><center>1</center></td><td>3 volts (Vcc)</td></tr>
<tr><td><center>2</center></td><td>Data IO, this needs a 5k
pull up resistor</td></tr>
<tr><td><center>3</center></td><td>Not connected</td></tr>
<tr><td><center>4</center></td><td>Ground</td></tr>
</table>
