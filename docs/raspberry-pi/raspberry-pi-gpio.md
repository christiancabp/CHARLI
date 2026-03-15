# Raspberry Pi GPIO Guide

An intro to General Purpose Input/Output (GPIO) pins — the magic that lets your Pi talk to the physical world. Covers all three boards in our inventory: **Pi 5**, **Pi Pico H / Pico 2WH**, and **Pi Zero 2 W**.

---

## What Are GPIO Pins?

GPIO = General Purpose Input/Output. They're the metal pins sticking out of your Pi. Each pin can be programmed to either:

- **Input**: Read signals from the outside world (buttons, sensors, switches)
- **Output**: Send signals to control things (LEDs, motors, buzzers, relays)

Think of them as tiny on/off switches your code can flip, or tiny microphones that listen for high/low voltage signals.

---

## The 40-Pin Header

The Pi 5, Pi Zero 2 W, and Pico boards all share a similar 40-pin GPIO header layout (Pi 5 and Zero 2 W are identical, Pico is different — see below).

### Pi 5 / Pi Zero 2 W — 40-Pin GPIO Pinout

```
                    +-----+-----+
               3V3  | 1   | 2   |  5V
     (SDA) GPIO  2  | 3   | 4   |  5V
     (SCL) GPIO  3  | 5   | 6   |  GND
            GPIO  4 | 7   | 8   |  GPIO 14 (TXD)
               GND  | 9   | 10  |  GPIO 15 (RXD)
            GPIO 17 | 11  | 12  |  GPIO 18 (PCM_CLK)
            GPIO 27 | 13  | 14  |  GND
            GPIO 22 | 15  | 16  |  GPIO 23
               3V3  | 17  | 18  |  GPIO 24
    (MOSI) GPIO 10  | 19  | 20  |  GND
    (MISO) GPIO  9  | 21  | 22  |  GPIO 25
    (SCLK) GPIO 11  | 23  | 24  |  GPIO  8 (CE0)
               GND  | 25  | 26  |  GPIO  7 (CE1)
     (ID_SD) GPIO 0 | 27  | 28  |  GPIO  1 (ID_SC)
            GPIO  5 | 29  | 30  |  GND
            GPIO  6 | 31  | 32  |  GPIO 12 (PWM0)
     (PWM1) GPIO 13 | 33  | 34  |  GND
     (PCM_FS) GPIO 19 | 35 | 36 |  GPIO 16
            GPIO 26 | 37  | 38  |  GPIO 20 (PCM_DIN)
               GND  | 39  | 40  |  GPIO 21 (PCM_DOUT)
                    +-----+-----+

        Left column = odd pins (1,3,5...)
        Right column = even pins (2,4,6...)
        Pin 1 is closest to the board edge (look for the square solder pad)
```

### Pin Types at a Glance

| Color Code | Pin Type | What It Does |
|---|---|---|
| Red | **5V Power** | 5 volts straight from the power supply. Can power small devices. |
| Orange | **3.3V Power** | 3.3 volts regulated. Most sensors and ICs want this. |
| Black | **Ground (GND)** | The return path for current. Every circuit needs one. |
| Green | **GPIO** | Programmable input/output pins. The ones you'll code with. |
| Blue | **Special Function** | I2C (SDA/SCL), SPI (MOSI/MISO/SCLK), UART (TX/RX), PWM |

### Key Concepts

- **BCM vs Physical numbering**: BCM = the GPIO number the chip uses. Physical = the literal pin position on the board. `gpiozero` uses BCM by default. Pin 29 on the board = GPIO 5 in code.
- **3.3V logic**: GPIO pins on Pi 5 and Zero 2 W are 3.3V. Sending 5V into a GPIO pin **will fry your Pi**. Always use a level shifter or voltage divider for 5V sensors.
- **Max current per pin**: ~16mA per GPIO pin. For anything needing more (motors, relays), use a transistor or motor driver.
- **Pull-up / Pull-down resistors**: Floating input pins read random noise. Use built-in pull-up/down resistors to set a default state.

---

## Board Comparison

| Feature | Pi 5 | Pi Zero 2 W | Pi Pico H | Pi Pico 2WH |
|---|---|---|---|---|
| **Type** | Single-board computer | Single-board computer | Microcontroller | Microcontroller |
| **CPU** | Arm Cortex-A76 (quad-core 2.4GHz) | Arm Cortex-A53 (quad-core 1GHz) | Arm Cortex-M0+ (dual-core 133MHz) | Arm Cortex-M33 (dual-core 150MHz) |
| **RAM** | 8GB | 512MB | 264KB | 520KB |
| **OS** | Raspberry Pi OS (Linux) | Raspberry Pi OS (Linux) | MicroPython / C/C++ | MicroPython / C/C++ |
| **GPIO Pins** | 40-pin header | 40-pin header | 40-pin header (different layout) | 40-pin header (different layout) |
| **GPIO Chip** | RP1 (new!) | BCM2835 | RP2040 | RP2350 |
| **WiFi** | Yes (Wi-Fi 5) | Yes (Wi-Fi 4) | No | Yes (Wi-Fi 4) |
| **Bluetooth** | Yes (BT 5.0) | Yes (BT 4.2) | No | Yes (BT 5.2) |
| **USB** | 2x USB 3.0 + 2x USB 2.0 | 1x micro USB (OTG) | 1x micro USB | 1x micro USB |
| **Best For** | Full computing, AI, server, display | Lightweight IoT, headless tasks | Sensor projects, real-time control | Wireless sensor projects, IoT |
| **Power** | 5V/5A USB-C | 5V/2.5A micro USB | 5V via USB or 1.8-5.5V via VSYS | 5V via USB or 1.8-5.5V via VSYS |

### When to Use What

- **Pi 5**: Your main brain. Runs Linux, Python, web servers, AI models. Use for CHARLI home hub, camera projects, anything needing a full OS.
- **Pi Zero 2 W**: Lightweight Linux in a tiny form factor. Perfect for standalone IoT gadgets, weather stations, or remote sensors that need Wi-Fi.
- **Pi Pico H**: Raw microcontroller. No OS, just your code running directly on metal. Perfect for real-time sensor reading, motor control, LED strips. The "H" means headers are pre-soldered.
- **Pi Pico 2WH**: Same as Pico but with Wi-Fi + Bluetooth + upgraded RP2350 chip. Best for wireless sensor nodes that report back to your Pi 5.

---

## Pi Pico Pinout (Different from Pi 5!)

The Pico has its own 40-pin layout. **Do not mix these up with Pi 5 pinouts.**

```
                         +-----USB-----+
                    GP0  | 1        40 |  VBUS (5V from USB)
                    GP1  | 2        39 |  VSYS (1.8-5.5V input)
                    GND  | 3        38 |  GND
                    GP2  | 4        37 |  3V3_EN
                    GP3  | 5        36 |  3V3 (OUT)
                    GP4  | 6        35 |  ADC_VREF
                    GP5  | 7        34 |  GP28 (ADC2)
                    GND  | 8        33 |  GND
                    GP6  | 9        32 |  GP27 (ADC1)
                    GP7  | 10       31 |  GP26 (ADC0)
                    GP8  | 11       30 |  RUN (reset)
                    GP9  | 12       29 |  GP22
                    GND  | 13       28 |  GND
                   GP10  | 14       27 |  GP21
                   GP11  | 15       26 |  GP20
                   GP12  | 16       25 |  GP19
                   GP13  | 17       24 |  GP18
                    GND  | 18       23 |  GND
                   GP14  | 19       22 |  GP17
                   GP15  | 20       21 |  GP16
                         +-------------+

    GP = General Purpose IO pin
    ADC = Analog-to-Digital Converter (read analog sensors!)
    VBUS = 5V from USB connection
    VSYS = System power input (1.8V to 5.5V)
    3V3 = 3.3V regulated output
```

### Pico Special Features

- **ADC pins (GP26-28)**: Can read analog values (0-3.3V) — Pi 5 can't do this natively!
- **PWM on every pin**: All GP pins support PWM for motor speed control, LED dimming, servo control
- **PIO (Programmable IO)**: Custom hardware-level protocols. Advanced but insanely powerful.
- **No OS overhead**: Your code runs instantly with microsecond timing precision

---

## Getting Started: Software Setup

### Pi 5 — Python with gpiozero

The Pi 5 uses a new **RP1** GPIO chip. The old `RPi.GPIO` library **does not work** on Pi 5. Use `gpiozero` with `lgpio` instead.

```bash
# Install (inside your .venv)
pip install gpiozero lgpio
```

```python
# blink_led.py — Blink an LED on GPIO 17
from gpiozero import LED
from time import sleep

led = LED(17)  # BCM pin number, NOT physical pin number

while True:
    led.on()
    sleep(1)
    led.off()
    sleep(1)
```

```python
# button_led.py — Press a button, light an LED
from gpiozero import LED, Button

led = LED(17)
button = Button(2)  # GPIO 2 with built-in pull-up

button.when_pressed = led.on
button.when_released = led.off

print("Press the button! Ctrl+C to exit.")
from signal import pause
pause()
```

```python
# read_sensor.py — Read a digital sensor
from gpiozero import DigitalInputDevice

sensor = DigitalInputDevice(4)  # GPIO 4

while True:
    if sensor.is_active:
        print("Sensor triggered!")
```

### Pi Zero 2 W — Same as Pi 5

The Zero 2 W uses the same `gpiozero` library and BCM pin numbering. The only difference is it uses the older `BCM2835` chip, so `RPi.GPIO` *does* work here — but stick with `gpiozero` for consistency across all your Pis.

```bash
pip install gpiozero
# lgpio may not be needed on Zero 2 W, but doesn't hurt to install
```

### Pi Pico — MicroPython

The Pico runs **MicroPython**, not regular Python. You flash it via USB and edit code with Thonny IDE or `mpremote`.

```bash
# Install mpremote on your Mac/Pi to interact with Pico over USB
pip install mpremote

# Connect to Pico REPL
mpremote connect auto

# Copy a file to the Pico
mpremote cp main.py :main.py

# Run a script on the Pico
mpremote run blink.py

# Reset the Pico
mpremote reset
```

```python
# blink.py — MicroPython on Pico
from machine import Pin
import time

led = Pin(25, Pin.OUT)  # Onboard LED (Pico H)
# Note: Pico 2WH onboard LED is on pin "LED" not 25

while True:
    led.toggle()
    time.sleep(0.5)
```

```python
# button.py — MicroPython on Pico
from machine import Pin
import time

led = Pin(15, Pin.OUT)
button = Pin(14, Pin.IN, Pin.PULL_UP)

while True:
    if button.value() == 0:  # Button pressed (pulled to ground)
        led.on()
    else:
        led.off()
    time.sleep(0.1)
```

```python
# analog_read.py — Read analog sensor (Pico only!)
from machine import ADC, Pin
import time

sensor = ADC(Pin(26))  # ADC0 on GP26

while True:
    raw = sensor.read_u16()  # 0-65535
    voltage = raw * 3.3 / 65535
    print(f"Raw: {raw}, Voltage: {voltage:.2f}V")
    time.sleep(1)
```

---

## Common Circuits

### 1. LED + Resistor (Output)

The "Hello World" of hardware. Every GPIO journey starts here.

```
GPIO 17 ──── [330 ohm resistor] ──── [LED +] ──── [LED -] ──── GND

Wiring:
  - GPIO 17 (physical pin 11) → resistor → LED long leg (anode)
  - LED short leg (cathode) → GND (physical pin 9)
  - ALWAYS use a resistor! Without it you'll burn out the LED or damage the GPIO pin.
  - 330 ohm is safe for most LEDs at 3.3V
```

### 2. Button (Input)

```
GPIO 2 ──── [Button] ──── GND

Wiring:
  - GPIO 2 (physical pin 3) → one leg of button
  - Other leg of button → GND (physical pin 6)
  - Enable internal pull-up resistor in code (gpiozero does this automatically)
  - When button is pressed: GPIO reads LOW (0)
  - When button is released: GPIO reads HIGH (1) via pull-up
```

### 3. Servo Motor (PWM Output)

```
GPIO 18 ──── [Servo signal wire (usually orange/white)]
5V ──────── [Servo power wire (usually red)]
GND ─────── [Servo ground wire (usually brown/black)]

Important:
  - Servos need 5V power, but the SIGNAL wire is 3.3V compatible
  - Don't power servos from GPIO pins — use the 5V rail
  - For multiple servos, use an external power supply
```

```python
# servo.py — Control a servo on Pi 5
from gpiozero import Servo
from time import sleep

servo = Servo(18)  # GPIO 18

while True:
    servo.min()     # -90 degrees
    sleep(1)
    servo.mid()     # 0 degrees (center)
    sleep(1)
    servo.max()     # +90 degrees
    sleep(1)
```

### 4. I2C Sensor (e.g., OLED Display, Temperature Sensor)

```
3V3 ──── [Sensor VCC]
GND ──── [Sensor GND]
GPIO 2 (SDA) ──── [Sensor SDA]
GPIO 3 (SCL) ──── [Sensor SCL]

Enable I2C first:
  sudo raspi-config nonint do_i2c 0

Detect connected I2C devices:
  i2cdetect -y 1
```

### 5. SPI Device (e.g., Mini PiTFT Display)

```
3V3 ──── [Device VCC]
GND ──── [Device GND]
GPIO 10 (MOSI) ──── [Device MOSI/SDA]
GPIO 11 (SCLK) ──── [Device SCK/SCL]
GPIO 8  (CE0)  ──── [Device CS]
GPIO 25        ──── [Device DC]
GPIO 24        ──── [Device RST]

Enable SPI first:
  sudo raspi-config nonint do_spi 0
```

---

## Safety Rules

1. **Never connect 5V to a GPIO pin.** GPIO pins are 3.3V. Applying 5V will permanently damage your Pi.
2. **Always use resistors with LEDs.** A bare LED on 3.3V will draw too much current and damage something.
3. **Max 16mA per GPIO pin.** For motors, relays, or anything power-hungry, use a transistor/MOSFET as a switch.
4. **Total GPIO current: ~50mA.** Don't light up 20 LEDs directly from GPIO. Use a driver IC or external power.
5. **Double-check your wiring before powering on.** A single wrong wire can fry components instantly.
6. **Disconnect power before rewiring.** Always shut down and unplug before changing any connections.
7. **Static electricity kills chips.** Touch a grounded metal surface before handling bare boards.

---

## Our Inventory: Quick Start Ideas

| Board | First Project | Difficulty |
|---|---|---|
| **Pi 5** | CHARLI Home Hub (already running!) | You're already here |
| **Pi 5 + Camera** | Motion detection + photo capture | Beginner |
| **Pi 5 + AI HAT+** | Real-time object detection | Intermediate |
| **Pi Zero 2 W** | Wireless temperature monitor | Beginner |
| **Pi Zero 2 W + Mini PiTFT** | Tiny status display (weather, system stats) | Beginner |
| **Pi Pico H** | LED blink → button → sensor reading | Start here for hardware |
| **Pi Pico H + Sensor Kit** | Environment monitor (temp, humidity, light) | Beginner |
| **Pi Pico 2WH** | Wireless sensor that reports to Pi 5 | Intermediate |
| **OLED Bonnet** | System dashboard with joystick navigation | Beginner |

---

## Troubleshooting

```bash
# "Permission denied" on GPIO
# On Pi 5, make sure you're in the gpio group:
sudo usermod -aG gpio $USER
# Then log out and back in

# I2C not detecting devices
# Make sure I2C is enabled:
sudo raspi-config nonint do_i2c 0
# Check wiring, then:
i2cdetect -y 1

# gpiozero says "pin factory not found"
# Install lgpio (required for Pi 5):
pip install lgpio

# Pico not showing up as USB device
# Hold BOOTSEL button while plugging in USB
# It should appear as a USB drive — drag .uf2 firmware onto it

# "RuntimeError: Cannot determine SOC peripheral base address"
# You're using RPi.GPIO on Pi 5. Switch to gpiozero + lgpio.
```

---

> **Remember**: The Pi 5 is a full Linux computer with GPIO. The Pico is a bare-metal microcontroller. Different tools, different superpowers. Use them together for maximum power.
