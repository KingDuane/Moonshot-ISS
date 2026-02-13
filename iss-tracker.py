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

# iss-tracker.py
"""
Realtime International Space Station Tracker for ESP32-S3-Touch-LCD-1.28
240x240 pixels, RGB565 color, SPI interface
"""
import network
import urequests
import math
import time
import os
from machine import Pin
import gc
from lcd_1inch28 import LCD_1inch28
from iss_icon import image_data, IMAGE_WIDTH, IMAGE_HEIGHT
from world_map import map_data, MAP_WIDTH, MAP_HEIGHT
from boot_logo import boot_image_data, BOOT_IMAGE_WIDTH, BOOT_IMAGE_HEIGHT

WIFI_SSID = "YOUR_SSID"
WIFI_PASSWORD = "YOUR_PASSWORD"
USER_LAT = 40.7128      # fallback if geolocation fails
USER_LON = -74.0060
UPDATE_INTERVAL = 30000
MAX_RADAR_DISTANCE = 12000

def draw_image(display, x, y, color=0xFFFF):
    """Draw ISS icon with specified color for the silhouette"""
    for i in range(IMAGE_HEIGHT):
        for j in range(IMAGE_WIDTH):
            if image_data[i * IMAGE_WIDTH + j] == 0xFFFF:
                display.pixel(x + j, y + i, color)

class ISSTracker:
    def __init__(self):
        self.lcd = LCD_1inch28()
        self.iss_data = {'lat': 0, 'lon': 0}
        self.last_update = 0
        self.trajectory_points = []
        self.max_trajectory_points = 1000
        self.sweep_angle = 0
        self._last_sweep_time = 0

        # BOOT button (GPIO 0) for screenshots
        self._screenshot_requested = False
        self._screenshot_count = self._count_existing_screenshots()
        self._screenshot_max = 10
        self._boot_btn = Pin(0, Pin.IN, Pin.PULL_UP)
        self._boot_btn.irq(trigger=Pin.IRQ_FALLING, handler=self._on_boot_press)

        self.lcd.set_bl_pwm(0)
        self.lcd.fill(0x0000)
        self.lcd.show()

    def _on_boot_press(self, pin):
        """ISR – just set a flag, no I/O allowed here."""
        self._screenshot_requested = True

    def _count_existing_screenshots(self):
        """Scan filesystem for existing screenshot_NNN.bin files to resume numbering."""
        count = 0
        try:
            for f in os.listdir('/'):
                if f.startswith('screenshot_') and f.endswith('.bin'):
                    count += 1
        except:
            pass
        return count

    def save_screenshot(self):
        """Save current framebuffer as raw RGB565 binary to flash."""
        if self._screenshot_count >= self._screenshot_max:
            print(f"Screenshot limit reached ({self._screenshot_max}). Delete files to free space.")
            return

        self._screenshot_count += 1
        filename = f"screenshot_{self._screenshot_count:03d}.bin"
        try:
            with open(filename, 'wb') as f:
                f.write(self.lcd.buffer)
            print(f"Screenshot saved: {filename} ({self._screenshot_count}/{self._screenshot_max})")
        except Exception as e:
            print(f"Screenshot failed: {e}")
            self._screenshot_count -= 1
            return

        # Visual feedback: brief backlight flash
        self.lcd.set_bl_pwm(0)
        time.sleep_ms(60)
        self.lcd.set_bl_pwm(65535)

    TINY_FONT = {
        '0': [0b111,
              0b101,
              0b101,
              0b101,
              0b111],
        '1': [0b010,
              0b110,
              0b010,
              0b010,
              0b111],
        '2': [0b111,
              0b001,
              0b111,
              0b100,
              0b111],
        '3': [0b111,
              0b001,
              0b111,
              0b001,
              0b111],
        '4': [0b101,
              0b101,
              0b111,
              0b001,
              0b001],
        '5': [0b111,
              0b100,
              0b111,
              0b001,
              0b111],
        '6': [0b111,
              0b100,
              0b111,
              0b101,
              0b111],
        '7': [0b111,
              0b001,
              0b010,
              0b010,
              0b010],
        '8': [0b111,
              0b101,
              0b111,
              0b101,
              0b111],
        '9': [0b111,
              0b101,
              0b111,
              0b001,
              0b111],
        '.': [0b000,
              0b000,
              0b000,
              0b000,
              0b010],
        'N': [0b101,
              0b111,
              0b111,
              0b111,
              0b101],
        'S': [0b111,
              0b100,
              0b111,
              0b001,
              0b111],
        'E': [0b111,
              0b100,
              0b111,
              0b100,
              0b111],
        'W': [0b101,
              0b101,
              0b101,
              0b101,
              0b111],
        ' ': [0b000,
              0b000,
              0b000,
              0b000,
              0b000],
        '-': [0b000,
              0b000,
              0b111,
              0b000,
              0b000],
    }

    def draw_tiny_char(self, char, x, y, color):
        """Draw a single character from the tiny font"""
        if char not in self.TINY_FONT:
            return x

        pattern = self.TINY_FONT[char]
        for row in range(5):
            for col in range(3):
                if pattern[row] & (1 << (2 - col)):
                    self.lcd.pixel(x + col, y + row, color)
        return x + 4

    def draw_tiny_text(self, text, x, y, color):
        """Draw a string using the tiny font"""
        current_x = x
        for char in text:
            current_x = self.draw_tiny_char(char, current_x, y, color)

    def line(self, x0, y0, x1, y1, color):
        """Draw a line using Bresenham's algorithm"""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1

        if dx > dy:
            err = dx / 2.0
            while x != x1:
                self.lcd.pixel(x, y, color)
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                self.lcd.pixel(x, y, color)
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        self.lcd.pixel(x, y, color)

    def circle(self, x0, y0, radius, color):
        """Draw a circle using Bresenham's algorithm"""
        x = radius
        y = 0
        err = 0

        while x >= y:
            self.lcd.pixel(x0 + x, y0 + y, color)
            self.lcd.pixel(x0 + y, y0 + x, color)
            self.lcd.pixel(x0 - y, y0 + x, color)
            self.lcd.pixel(x0 - x, y0 + y, color)
            self.lcd.pixel(x0 - x, y0 - y, color)
            self.lcd.pixel(x0 - y, y0 - x, color)
            self.lcd.pixel(x0 + y, y0 - x, color)
            self.lcd.pixel(x0 + x, y0 - y, color)

            y += 1
            if err <= 0:
                err += 2 * y + 1
            if err > 0:
                x -= 1
                err -= 2 * x + 1

    def draw_sweep(self, center_x, center_y, angle, radius):
        """Draw radar sweep line"""
        rad = math.radians(angle)
        x = center_x + int(radius * math.sin(rad))
        y = center_y - int(radius * math.cos(rad))
        self.line(center_x, center_y, x, y, 0xFFFF)

    def is_sweep_near_iss(self, sweep_angle, iss_bearing, tolerance=12):
        """Check if sweep intersects with ISS icon area"""
        diff = abs(sweep_angle - iss_bearing)
        if diff > 180:
            diff = 360 - diff

        return diff <= tolerance

    def boot_animation(self):
        self.lcd.fill(0x0000)
        logo_x = (240 - BOOT_IMAGE_WIDTH) // 2
        logo_y = (240 - BOOT_IMAGE_HEIGHT) // 2

        for _ in range(2):
            self.draw_logo(self.lcd, boot_image_data, logo_x, logo_y, BOOT_IMAGE_WIDTH, BOOT_IMAGE_HEIGHT, 0xFFFF)
            self.lcd.show()
            self.lcd.set_bl_pwm(65535)
            time.sleep_ms(1000)
            self.lcd.set_bl_pwm(0)
            self.lcd.fill(0x0000)
            self.lcd.show()
            time.sleep_ms(500)

        self.draw_logo(self.lcd, boot_image_data, logo_x, logo_y, BOOT_IMAGE_WIDTH, BOOT_IMAGE_HEIGHT, 0xFFFF)
        self.lcd.show()
        self.fade_backlight(0, 65535)

    def draw_logo(self, display, image_data, x, y, width, height, color=0xFFFF):
        """Draw a logo with specified color."""
        for i in range(height):
            for j in range(width):
                if image_data[i * width + j] == 0xFFFF:
                    display.pixel(x + j, y + i, color)

    def fade_backlight(self, start=0, end=65535, steps=50, delay_ms=20):
        for i in range(steps):
            level = start + (end - start) * i // steps
            self.lcd.set_bl_pwm(level)
            time.sleep_ms(delay_ms)

    def pulse_screen(self):
        """Create a subtle pulse effect"""
        PULSE_CYCLES = 4
        STEP_DELAY = 5

        for i in range(PULSE_CYCLES):
            intensity = int((math.sin(i * math.pi / PULSE_CYCLES) + 1) * 127)
            overlay_color = (intensity << 11) | (intensity << 5) | intensity

            for y in range(0, 240, 4):
                for x in range(0, 240, 4):
                    current = self.lcd.pixel(x, y)
                    blended = ((current & overlay_color) >> 1) & 0xFFFF
                    self.lcd.pixel(x, y, blended)

            self.lcd.show()
            time.sleep_ms(STEP_DELAY)

    def fetch_location(self):
        """Fetch approximate location via IP geolocation"""
        global USER_LAT, USER_LON
        try:
            response = urequests.get('http://ip-api.com/json/?fields=lat,lon')
            data = response.json()
            response.close()
            USER_LAT = data['lat']
            USER_LON = data['lon']
            print(f"Geolocation: {USER_LAT}, {USER_LON}")
            gc.collect()
        except:
            print("Geolocation failed, using fallback coordinates")

    def connect_wifi(self):
        """Connect to WiFi network with visual feedback"""
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)

        if not wlan.isconnected():
            print('Connecting to WiFi...')
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)

            while not wlan.isconnected():
                self.pulse_screen()
                time.sleep_ms(5)

    def handle_connection_loss(self):
        """Invert screen to indicate connection loss"""
        for y in range(240):
            for x in range(240):
                pixel = self.lcd.pixel(x, y)
                self.lcd.pixel(x, y, ~pixel & 0xFFFF)
        self.lcd.show()

    def fetch_iss_data(self):
        """Fetch ISS position from API"""
        try:
            response = urequests.get('http://api.open-notify.org/iss-now.json')
            data = response.json()
            response.close()
            self.iss_data = {
                'lat': float(data['iss_position']['latitude']),
                'lon': float(data['iss_position']['longitude'])
            }
            return True
        except:
            return False


    def calculate_position(self):
        """Calculate ISS position with basic spherical geometry"""
        earth_radius = 6371  # km
        iss_altitude = 408  # km

        try:
            obs_lat = math.radians(USER_LAT)
            obs_lon = math.radians(USER_LON)
            iss_lat = math.radians(self.iss_data['lat'])
            iss_lon = math.radians(self.iss_data['lon'])

            dlat = iss_lat - obs_lat
            dlon = iss_lon - obs_lon

            a = math.sin(dlat/2)**2 + \
                math.cos(obs_lat) * math.cos(iss_lat) * \
                math.sin(dlon/2)**2

            great_circle_dist = 2 * earth_radius * math.asin(math.sqrt(max(min(a, 1), 0)))
            slant_range = math.sqrt(great_circle_dist**2 + iss_altitude**2)

            y = math.sin(dlon) * math.cos(iss_lat)
            x = math.cos(obs_lat) * math.sin(iss_lat) - \
                math.sin(obs_lat) * math.cos(iss_lat) * math.cos(dlon)
            bearing = math.degrees(math.atan2(y, x)) % 360

            return slant_range, bearing

        except Exception as e:
            print(f"Error in calculate_position: {e}")
            return 1000, 0

    def draw_world_map(self):
        """Draw world map as background with horizontal wrapping"""
        x_offset = int(MAP_WIDTH/2 + (USER_LON * MAP_WIDTH/360))
        y_offset = int(MAP_HEIGHT/2 - (USER_LAT * MAP_HEIGHT/180))

        start_x = 120 - x_offset + 16
        start_y = 120 - y_offset - 50

        map_color = 0x6631

        for screen_y in range(0, 240, 2):
            map_y = screen_y - start_y
            if 0 <= map_y < MAP_HEIGHT:
                for screen_x in range(0, 240, 2):
                    map_x = (screen_x - start_x) % MAP_WIDTH
                    byte_index = (map_y * MAP_WIDTH + map_x) // 8
                    bit_index = 7 - ((map_y * MAP_WIDTH + map_x) % 8)
                    if byte_index < len(map_data):
                        if map_data[byte_index] & (1 << bit_index):
                            self.lcd.pixel(screen_x, screen_y, map_color)

    def draw_radar(self):
        """Main loop"""
        current_time = time.ticks_ms()
        center_x, center_y = 120, 120

        elapsed = time.ticks_diff(current_time, self._last_sweep_time)
        self._last_sweep_time = current_time
        elapsed = min(elapsed, 100)  # cap to avoid jump after fetch pause
        self.sweep_angle = (self.sweep_angle + elapsed / 50) % 360
        sweep_angle = int(self.sweep_angle)

        self.lcd.fill(0x0000)

        self.draw_world_map()

        if len(self.trajectory_points) > 1:
            dash_length = 3
            gap_length = 3

            for i in range(len(self.trajectory_points) - 1):
                x0, y0, t0 = self.trajectory_points[i]
                x1, y1, t1 = self.trajectory_points[i + 1]

                dx = x1 - x0
                dy = y1 - y0
                distance = math.sqrt(dx * dx + dy * dy)

                if distance > 30:
                    continue

                if distance > 0:
                    num_segments = int(distance / 6)
                    num_segments = max(num_segments, 1)

                    for j in range(num_segments):
                        t_start = j * (dash_length + gap_length) / distance
                        t_end = min((j * (dash_length + gap_length) + dash_length) / distance, 1.0)

                        x_start = int(x0 + dx * t_start + 0.5)
                        y_start = int(y0 + dy * t_start + 0.5)
                        x_end = int(x0 + dx * t_end + 0.5)
                        y_end = int(y0 + dy * t_end + 0.5)

                        self.line(x_start, y_start, x_end, y_end, 0xE739)

        self.line(center_x, 0, center_x, center_y, 0xFFFF)
        self.line(center_x - 8, center_y, center_x + 8, center_y, 0xFFFF)

        for radius in [30, 60, 90]:
            self.circle(center_x, center_y, radius, 0xFFFF)

        self.draw_sweep(center_x, center_y, sweep_angle, 120)

        distance, bearing = self.calculate_position()
        rad_bearing = math.radians(bearing)

        screen_radius = 120
        arrow_buffer = 10

        scaled_distance = min((distance / 100), screen_radius)
        iss_in_range = distance <= MAX_RADAR_DISTANCE

        if iss_in_range:
            x = center_x + scaled_distance * math.sin(rad_bearing)
            y = center_y - scaled_distance * math.cos(rad_bearing)

            if len(self.trajectory_points) == 0 or (
                abs(self.trajectory_points[-1][0] - x) > 5 or
                abs(self.trajectory_points[-1][1] - y) > 5
            ):
                self.trajectory_points.append((int(x), int(y), current_time))
                if len(self.trajectory_points) > self.max_trajectory_points:
                    self.trajectory_points.pop(0)

            icon_x = int(x - IMAGE_WIDTH // 2)
            icon_y = int(y - IMAGE_HEIGHT // 2)
            draw_image(self.lcd, icon_x, icon_y, 0xFFFF)

            if self.is_sweep_near_iss(sweep_angle, bearing):
                lat = self.iss_data['lat']
                lon = self.iss_data['lon']
                lat_str = f"{abs(lat):.1f}{'N' if lat >= 0 else 'S'}"
                lon_str = f"{abs(lon):.1f}{'E' if lon >= 0 else 'W'}"

                text_y = icon_y + IMAGE_HEIGHT + 1
                self.draw_tiny_text(lat_str, icon_x, text_y, 0xFFFF)
                self.draw_tiny_text(lon_str, icon_x, text_y + 6, 0xFFFF)

        else:
            radius = screen_radius - arrow_buffer
            marker_size = 10

            base_x = center_x + radius * math.sin(rad_bearing)
            base_y = center_y - radius * math.cos(rad_bearing)

            right_angle = rad_bearing - 3 * math.pi / 4
            right_x = base_x + marker_size * math.sin(right_angle)
            right_y = base_y - marker_size * math.cos(right_angle)

            left_angle = rad_bearing + 3 * math.pi / 4
            left_x = base_x + marker_size * math.sin(left_angle)
            left_y = base_y - marker_size * math.cos(left_angle)

            self.line(int(base_x), int(base_y), int(right_x), int(right_y), 0xFFFF)
            self.line(int(base_x), int(base_y), int(left_x), int(left_y), 0xFFFF)

            if self.is_sweep_near_iss(sweep_angle, bearing):
                lat = self.iss_data['lat']
                lon = self.iss_data['lon']
                lat_str = f"{abs(lat):.1f}{'N' if lat >= 0 else 'S'}"
                lon_str = f"{abs(lon):.1f}{'E' if lon >= 0 else 'W'}"

                text_x = int(base_x)
                text_y = int(base_y + 8)
                self.draw_tiny_text(lat_str, text_x, text_y, 0xFFFF)
                self.draw_tiny_text(lon_str, text_x, text_y + 6, 0xFFFF)

        self.lcd.show()

    def run(self):
        """Main loop"""
        try:
            self.boot_animation()
            self.connect_wifi()
            self.fetch_location()

            start_time = time.ticks_ms()
            self.last_update = start_time
            last_wifi_check = start_time
            WIFI_CHECK_INTERVAL = 2000
            wifi_connected = True

            self.fetch_iss_data()

            while True:
                current_time = time.ticks_ms()

                if time.ticks_diff(current_time, last_wifi_check) >= WIFI_CHECK_INTERVAL:
                    current_wifi_state = network.WLAN(network.STA_IF).isconnected()
                    if current_wifi_state != wifi_connected:
                        print("WiFi state changed:", "Connected" if current_wifi_state else "Disconnected")
                        if not current_wifi_state:
                            self.handle_connection_loss()
                        wifi_connected = current_wifi_state
                    last_wifi_check = current_time

                if time.ticks_diff(current_time, self.last_update) >= UPDATE_INTERVAL:
                    self.fetch_iss_data()
                    self.last_update = current_time
                    gc.collect()

                self.draw_radar()

                if self._screenshot_requested:
                    self._screenshot_requested = False
                    self.save_screenshot()

                time.sleep_ms(25)

        except KeyboardInterrupt:
            print("\nExiting gracefully...")
        except Exception as e:
            print(f"Runtime error: {e}")
        finally:
            self.lcd.set_bl_pwm(0)

if __name__ == '__main__':
    tracker = ISSTracker()
    tracker.run()
