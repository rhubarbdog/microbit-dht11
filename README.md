# microbit-dht11
a *nearly working* DHT11 class for microbit

This nearly works I've posted it so intrested parties can try and get it working

The code is partially complete it only works in `microbit.pin0`

The .read method is too slow at switching between write mode (trigger the sensor)
and read mode (grabbing the bit stream)

The bits are grabbed with a `Thumb assembly` routine

Please feel free to try and get this up and running.
