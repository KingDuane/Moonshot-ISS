'''
                    @         @                 @@@@@       @         @@@@@@@@@@
                  @@@       @@@             @@@@@@@@@@@@@   @@@       @@@@@@@@@@
               @@@@@@    @@@@@@           @@@@@@@@@@@@@@@@@ @@@@@@    @@@@@@@@@@
             @@@@@@@@  @@@@@@@@          @@@@@@@@@@@@@@@@@@@@@@@@@@@  @@@@@@@@@@
          @@@@@@@@@@@@@@@@@@@@@   @@@   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@@@@@@@@@@@@@@@X@@@@@@@@@ @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
     @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ @@@@@@@@@@@@@@@@@ @@@@@@@@@@@@@@@@@@@@
   @@@@@@@@@@@@@@@@@@@@@@@@@@@X@@@@@@@@@    @@@@@@@@@@@@@   @@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@    @@@           @@@@@       @@@@@@@@@@@@@@@@@@@@

                  @@@@@@      @@@@@@@@@@@@@@@@@@@@          @@@@@@@@@@@@@@@@@@@@
              @@@@@@@@@@@@@   @@@@@@@@@@@@@@@@@@@@          @@@@@@@@@@@@@@@@@@@@
            @@@@@@@@@@@@@@@@@ @@@@@@@@@@@@@@@@@@@@    @@@   @@@@@@@@@@@@@@@@@@@@
           @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ @@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@         @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@     @@@@@@@@@@     
 @@@@@@@@@@@@@@@@@@@          @@@@@@@@@@@@@@@@@@@@ @@@@@@@@@     @@@@@@@@@@     
   @@@@@@@@@@@@@@@            @@@@@@@@@@@@@@@@@@@@    @@@        @@@@@@@@@@     
      @@@@@@@@                @@@@@@@@@@@@@@@@@@@@               @@@@@@@@@@     
'''

# lcd_1inch28.py
"""
Waveshare 1.28inch LCD display driver for ESP32-S3-Touch-LCD-1.28
240x240 pixels, RGB565 color, SPI interface
"""
from machine import Pin, SPI, PWM
import framebuf
import time

# Pin definitions from working demo
TFT_DC = 8    
TFT_CS = 9    
TFT_CLK = 10  
TFT_MOSI = 11
TFT_RST = 14
TFT_BL = 2

class LCD_1inch28(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 240
        self.height = 240
        
        print("Setting up pins...")
        self.cs = Pin(TFT_CS, Pin.OUT)
        self.rst = Pin(TFT_RST, Pin.OUT)
        self.dc = Pin(TFT_DC, Pin.OUT)
        
        # Setup backlight PWM - start with backlight off
        self.bl = Pin(TFT_BL, Pin.OUT)
        self.pwm = PWM(self.bl)
        self.pwm.freq(1000)
        self.set_bl_pwm(0)  # Start with backlight off
        
        print("Starting display init...")
        self.spi = SPI(2,
                      baudrate=80000000, 
                      polarity=0,
                      phase=0,
                      sck=Pin(TFT_CLK),
                      mosi=Pin(TFT_MOSI))
        
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        
        # Hardware reset
        self.rst.value(1)
        time.sleep_ms(50)
        self.rst.value(0)
        time.sleep_ms(50)
        self.rst.value(1)
        time.sleep_ms(50)
        
        self.init_display()
        self.fill(0xFFFF)  # Fill white
        self.show()

    def init_display(self):
        """Initialize GC9A01 display"""
        self.write_cmd(0xEF)
        self.write_cmd(0xEB)
        self.write_data(0x14)

        self.write_cmd(0xFE)
        self.write_cmd(0xEF)

        self.write_cmd(0xEB)
        self.write_data(0x14)

        self.write_cmd(0x84)
        self.write_data(0x40)

        self.write_cmd(0x85)
        self.write_data(0xFF)

        self.write_cmd(0x86)
        self.write_data(0xFF)

        self.write_cmd(0x87)
        self.write_data(0xFF)

        self.write_cmd(0x88)
        self.write_data(0x0A)

        self.write_cmd(0x89)
        self.write_data(0x21)

        self.write_cmd(0x8A)
        self.write_data(0x00)

        self.write_cmd(0x8B)
        self.write_data(0x80)

        self.write_cmd(0x8C)
        self.write_data(0x01)

        self.write_cmd(0x8D)
        self.write_data(0x01)

        self.write_cmd(0x8E)
        self.write_data(0xFF)

        self.write_cmd(0x8F)
        self.write_data(0xFF)

        self.write_cmd(0xB6)
        self.write_data(0x00)
        self.write_data(0x00)

        self.write_cmd(0x36)
        self.write_data(0x40)

        self.write_cmd(0x3A)
        self.write_data(0x05)

        self.write_cmd(0x90)
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x08)

        self.write_cmd(0xBD)
        self.write_data(0x06)

        self.write_cmd(0xBC)
        self.write_data(0x00)

        self.write_cmd(0xFF)
        self.write_data(0x60)
        self.write_data(0x01)
        self.write_data(0x04)

        self.write_cmd(0xC3)
        self.write_data(0x13)
        self.write_cmd(0xC4)
        self.write_data(0x13)

        self.write_cmd(0xC9)
        self.write_data(0x22)

        self.write_cmd(0xBE)
        self.write_data(0x11)

        self.write_cmd(0xE1)
        self.write_data(0x10)
        self.write_data(0x0E)

        self.write_cmd(0xDF)
        self.write_data(0x21)
        self.write_data(0x0c)
        self.write_data(0x02)

        self.write_cmd(0xF0)
        self.write_data(0x45)
        self.write_data(0x09)
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x26)
        self.write_data(0x2A)

        self.write_cmd(0xF1)
        self.write_data(0x43)
        self.write_data(0x70)
        self.write_data(0x72)
        self.write_data(0x36)
        self.write_data(0x37)
        self.write_data(0x6F)

        self.write_cmd(0xF2)
        self.write_data(0x45)
        self.write_data(0x09)
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x26)
        self.write_data(0x2A)

        self.write_cmd(0xF3)
        self.write_data(0x43)
        self.write_data(0x70)
        self.write_data(0x72)
        self.write_data(0x36)
        self.write_data(0x37)
        self.write_data(0x6F)

        self.write_cmd(0xED)
        self.write_data(0x1B)
        self.write_data(0x0B)

        self.write_cmd(0xAE)
        self.write_data(0x77)

        self.write_cmd(0xCD)
        self.write_data(0x63)

        self.write_cmd(0x70)
        self.write_data(0x07)
        self.write_data(0x07)
        self.write_data(0x04)
        self.write_data(0x0E)
        self.write_data(0x0F)
        self.write_data(0x09)
        self.write_data(0x07)
        self.write_data(0x08)
        self.write_data(0x03)

        self.write_cmd(0xE8)
        self.write_data(0x34)

        self.write_cmd(0x62)
        self.write_data(0x18)
        self.write_data(0x0D)
        self.write_data(0x71)
        self.write_data(0xED)
        self.write_data(0x70)
        self.write_data(0x70)
        self.write_data(0x18)
        self.write_data(0x0F)
        self.write_data(0x71)
        self.write_data(0xEF)
        self.write_data(0x70)
        self.write_data(0x70)

        self.write_cmd(0x63)
        self.write_data(0x18)
        self.write_data(0x11)
        self.write_data(0x71)
        self.write_data(0xF1)
        self.write_data(0x70)
        self.write_data(0x70)
        self.write_data(0x18)
        self.write_data(0x13)
        self.write_data(0x71)
        self.write_data(0xF3)
        self.write_data(0x70)
        self.write_data(0x70)

        self.write_cmd(0x64)
        self.write_data(0x28)
        self.write_data(0x29)
        self.write_data(0xF1)
        self.write_data(0x01)
        self.write_data(0xF1)
        self.write_data(0x00)
        self.write_data(0x07)

        self.write_cmd(0x66)
        self.write_data(0x3C)
        self.write_data(0x00)
        self.write_data(0xCD)
        self.write_data(0x67)
        self.write_data(0x45)
        self.write_data(0x45)
        self.write_data(0x10)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)

        self.write_cmd(0x67)
        self.write_data(0x00)
        self.write_data(0x3C)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x01)
        self.write_data(0x54)
        self.write_data(0x10)
        self.write_data(0x32)
        self.write_data(0x98)

        self.write_cmd(0x74)
        self.write_data(0x10)
        self.write_data(0x85)
        self.write_data(0x80)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x4E)
        self.write_data(0x00)

        self.write_cmd(0x98)
        self.write_data(0x3e)
        self.write_data(0x07)

        self.write_cmd(0x35)
        self.write_cmd(0x21)

        self.write_cmd(0x11)
        time.sleep_ms(120)

        self.write_cmd(0x29)
        time.sleep_ms(20)

    def write_cmd(self, cmd):
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytes([cmd]))
        self.cs.value(1)

    def write_data(self, data):
        self.cs.value(0)
        self.dc.value(1)
        self.spi.write(bytes([data]))
        self.cs.value(1)

    def set_bl_pwm(self, duty):
        self.pwm.duty_u16(duty)

    def fade_in_backlight(self, target_duty=65535, duration_ms=1000):
        steps = 60
        for i in range(steps + 1):
            duty = int(target_duty * (i / steps))
            self.set_bl_pwm(duty)
            time.sleep_ms(duration_ms // steps)

    def show(self):
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xef)
        
        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xef)
        
        self.write_cmd(0x2C)
        
        self.cs.value(0)
        self.dc.value(1)
        self.spi.write(self.buffer)
        self.cs.value(1)