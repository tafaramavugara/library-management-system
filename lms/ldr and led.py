from machine import Pin, ADC
import time

led_pin = Pin(0, Pin.OUT)        # GP15 for the LED
ldr_pin = ADC(0)                  # GP26 is ADC0 for the LDR

threshold = 500
while True:
    ldr_value = ldr_pin.read_u16()
    print("LDR Value:", ldr_value)
    
    if ldr_value < threshold:
        led_pin.value(1)  # Turn on LEDs
        time.sleep(3)
    else:
            led_pin.value(0)  # Turn off LEDs
            time.sleep(4)
