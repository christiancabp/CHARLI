# Discover: What Can We Build?

Ideas and project inspiration for our Raspberry Pi inventory. Organized by category, tagged by difficulty and which boards to use. Everything here is buildable with what we already own (or with minimal extra parts).

---

## Software & Networking

### Pi-Powered Home Dashboard
**Boards**: Pi 5 + 7" Touchscreen | **Difficulty**: Beginner

A live dashboard on the touchscreen showing weather, calendar, news headlines, system stats, and CHARLI's status. Think a smart mirror without the mirror. Built with a simple web app served by FastAPI. Could even show your daughter's school schedule.

### Personal VPN / Ad Blocker (Pi-hole)
**Boards**: Pi Zero 2 W | **Difficulty**: Beginner

Turn a Pi Zero into a network-wide ad blocker. Every device on your Wi-Fi gets ad-free browsing without installing anything on them. Takes 15 minutes to set up.

### Private Git Server
**Boards**: Pi 5 (NVMe) | **Difficulty**: Intermediate

Run Gitea or Forgejo on your Pi 5 with the NVMe SSD. Your own private GitHub at home. Good for family projects, private repos, or just learning how Git servers work under the hood.

### Retro Game Console
**Boards**: Pi 5 or Pi Zero 2 W | **Difficulty**: Beginner

Install RetroPie or Batocera and play classic Nintendo, SNES, and arcade games on the touchscreen. A fun weekend project with your daughter. The Pi 5 can even handle N64 and PSP games.

### Network Monitoring Station
**Boards**: Pi Zero 2 W + OLED Bonnet | **Difficulty**: Intermediate

A tiny always-on device that monitors your home network. Shows connected devices, bandwidth usage, and alerts on the OLED display. Joystick to navigate through screens.

### Self-Hosted n8n Node
**Boards**: Pi 5 | **Difficulty**: Intermediate

Run an n8n automation instance directly on the Pi 5. Trigger home automations, send notifications, or chain together APIs — all from your local network.

---

## AI & Machine Learning

### Real-Time Object Detection
**Boards**: Pi 5 + Camera Module 3 + AI HAT+ | **Difficulty**: Intermediate

Use the AI HAT+ (13 TOPS) to run object detection models in real time. Point the camera at your desk and identify objects, count things, or detect when someone enters the room. The camera's wide-angle lens is perfect for this.

### CHARLI Vision — "What Am I Looking At?"
**Boards**: Pi 5 + Camera Module 3 + AI HAT+ | **Difficulty**: Intermediate

Extend CHARLI with vision. Say "Hey Charli, what do you see?" and it captures a photo, runs it through a vision model, and describes what's in front of it. Could use the AI HAT+ for on-device inference or send the image to Claude's vision API.

### Face Detection Greeter
**Boards**: Pi 5 + Camera Module 3 | **Difficulty**: Intermediate

The Pi detects when someone is in front of it and greets them. With a bit more work, it can learn to recognize family members and give personalized greetings. "Good morning, welcome back!"

### Voice-Controlled Smart Desk
**Boards**: Pi 5 + USB Mic + Speaker | **Difficulty**: Already started!

This is basically CHARLI Home evolved. Add commands like "turn on the desk lamp" (via smart plug API or Pico-controlled relay), "play some music," or "what's on my calendar today?"

### Gesture Recognition
**Boards**: Pi 5 + Camera + AI HAT+ | **Difficulty**: Advanced

Use MediaPipe or a custom model on the AI HAT+ to recognize hand gestures. Wave to dismiss a notification, thumbs up to confirm, point to select. Sci-fi desk interaction.

### Local LLM Experiments
**Boards**: Pi 5 (8GB) | **Difficulty**: Intermediate

Run small language models (TinyLlama, Phi-2) locally on the Pi 5 with llama.cpp. They won't be as smart as Claude, but it's educational to see how LLMs work at the edge. Good for understanding model quantization, inference speed, and hardware limits.

---

## Robotics

### Desk Robot Arm (Servo Kit)
**Boards**: Pi Pico H + Sensor Kit (servos) | **Difficulty**: Intermediate

Build a simple robotic arm from servos in the sensor kit. Control it from the Pico with MicroPython. Later, connect it to the Pi 5 so CHARLI can control it with voice commands. "Charli, hand me the pen."

### Line-Following Robot
**Boards**: Pi Pico 2WH + IR sensors from kit | **Difficulty**: Beginner

Classic robotics starter. Use IR sensors to follow a black line on white paper. Teaches PID control, sensor reading, and motor driving. Your daughter can draw the track with a marker.

### Obstacle-Avoiding Bot
**Boards**: Pi Pico 2WH + Ultrasonic sensor from kit | **Difficulty**: Beginner

A small robot that drives forward and turns when it detects an obstacle. Simple, visual, and satisfying. Add the OLED display to show distance readings.

### Remote-Control Car (Wi-Fi)
**Boards**: Pi Pico 2WH + motors | **Difficulty**: Intermediate

Build a car controlled from a web page on your phone. The Pico 2WH's Wi-Fi serves a simple page with arrow buttons. Tap to drive. Could later add the camera for FPV (first-person view) driving via the Pi 5.

### Balancing Robot
**Boards**: Pi Pico H + MPU6050 accelerometer/gyroscope | **Difficulty**: Advanced

A two-wheeled robot that balances itself like a Segway. Teaches PID control, real-time sensor fusion, and motor control. One of the most rewarding robotics projects when it finally balances.

### CHARLI Bot — Mobile Extension
**Boards**: Pi Zero 2 W + motors + camera | **Difficulty**: Advanced

A small mobile robot that CHARLI controls. Roams around, streams video back to the Pi 5, and responds to voice commands. "Charli, go check if I left the garage door open." Future project, but a good north star.

---

## Aerospace & Space

### Weather Station + Data Logger
**Boards**: Pi Pico 2WH + BME280 sensor (temp/humidity/pressure) | **Difficulty**: Beginner

Log temperature, humidity, and barometric pressure over time. Display live readings on the Mini PiTFT. Send data wirelessly to the Pi 5 for graphing. Teaches data collection, the basics of meteorology, and how real weather stations work.

### High-Altitude Balloon Tracker
**Boards**: Pi Zero 2 W + GPS module + camera | **Difficulty**: Advanced

Track a weather balloon's GPS position and capture photos from near-space (100,000 feet). The Pi Zero is light enough for balloon payloads. This is a real aerospace project — schools and hobbyists do this. You get back photos of the curvature of the Earth.

### Star Tracker / Constellation Identifier
**Boards**: Pi 5 + Camera Module 3 | **Difficulty**: Intermediate

Point the camera at the night sky and identify constellations, planets, and satellites in real time. Use plate-solving algorithms (like astrometry.net) or train a model on the AI HAT+. Educational and genuinely beautiful.

### ISS Tracker
**Boards**: Pi Zero 2 W + OLED Bonnet or Mini PiTFT | **Difficulty**: Beginner

Track the International Space Station in real time using public APIs. Show its position on the tiny display. Buzz or light up an LED when the ISS is passing overhead. The joystick on the OLED Bonnet can switch between views.

### Rocket Telemetry Logger
**Boards**: Pi Pico H + accelerometer + barometer | **Difficulty**: Intermediate

Mount inside a model rocket to log acceleration, altitude, rotation, and temperature during flight. The Pico is tiny, light, and boots instantly — perfect for rocketry. After recovery, plug it into USB and download the flight data for analysis.

### Satellite Ground Station
**Boards**: Pi 5 + RTL-SDR dongle (cheap USB radio) | **Difficulty**: Advanced

Receive signals from actual satellites passing overhead — weather satellites (NOAA), amateur radio satellites, even the ISS. With an RTL-SDR dongle (~$25) and a simple antenna, you can decode weather satellite images directly from space. This is real radio astronomy.

### Sun Tracker with Solar Panel
**Boards**: Pi Pico H + 2 servos + light sensors + small solar panel | **Difficulty**: Intermediate

Build a mount that tracks the sun across the sky to keep a small solar panel at the optimal angle. Uses light-dependent resistors to find the brightest direction. Teaches solar energy, servo control, and feedback loops.

---

## IoT & Home Automation

### Smart Desk Lamp
**Boards**: Pi Pico 2WH + relay module | **Difficulty**: Beginner

Control a desk lamp with voice ("Hey Charli, lights on") or from a web page. The Pico 2WH connects to Wi-Fi and listens for commands from the Pi 5. Could also auto-dim based on ambient light sensor readings.

### Room Temperature Monitor Network
**Boards**: 2x Pi Pico 2WH + temperature sensors | **Difficulty**: Beginner

Place a Pico in different rooms, each with a temperature sensor. They wirelessly report temperatures to the Pi 5, which displays them on the CHARLI dashboard. First real IoT project — multiple devices talking to a central hub.

### Plant Watering System
**Boards**: Pi Pico H + soil moisture sensor + water pump | **Difficulty**: Intermediate

Measure soil moisture and automatically water a plant when it's too dry. Display status on the Mini PiTFT. Log watering history. Your daughter can take care of a plant with robot help.

### Door/Window Sensor
**Boards**: Pi Pico 2WH + magnetic reed switch | **Difficulty**: Beginner

Detect when a door or window opens and send a notification to the Pi 5. CHARLI announces: "The front door was just opened." Simple, useful, and a great intro to wireless sensor networks.

### Motion-Activated Camera
**Boards**: Pi Zero 2 W + Camera or Pi 5 + Camera | **Difficulty**: Beginner

Detect motion using the camera (frame differencing) and capture a photo or short video. Send a notification. Useful as a simple security camera or wildlife cam for the backyard.

---

## Creative & Fun

### Digital Photo Frame
**Boards**: Pi Zero 2 W + 7" Touchscreen | **Difficulty**: Beginner

A digital photo frame that cycles through family photos. Swipe to change photos on the touchscreen. Could pull from a shared Google Photos album or a local folder synced via rsync.

### LED Matrix Pixel Art
**Boards**: Pi Pico H + WS2812B LED strip/matrix | **Difficulty**: Beginner

Create pixel art, animations, or a clock on an LED matrix. Your daughter can design pixel art characters and see them light up. Teaches addressable LEDs and color theory.

### MIDI Controller
**Boards**: Pi Pico H + buttons + potentiometers from sensor kit | **Difficulty**: Intermediate

Turn the Pico into a USB MIDI controller. Press buttons to play notes, turn knobs to adjust effects. Plug into GarageBand or any music software. The Pico natively supports USB HID/MIDI.

### Reaction Time Game
**Boards**: Pi Pico H + LEDs + buttons from sensor kit | **Difficulty**: Beginner

An LED lights up at a random time — slap the button as fast as you can. Display your reaction time on the Mini PiTFT. Compete for the fastest time. Great first project with your daughter.

### Simon Says Game
**Boards**: Pi Pico H + 4 LEDs + 4 buttons + buzzer from sensor kit | **Difficulty**: Beginner

The classic memory game. LEDs flash a pattern, you repeat it by pressing buttons. Gets faster and longer each round. Teaches arrays, loops, and input handling.

### Digital Pet (Tamagotchi)
**Boards**: Pi Pico H + Mini PiTFT or OLED Bonnet | **Difficulty**: Intermediate

A virtual pet that lives on the tiny screen. Feed it, play with it, watch it grow. Uses the joystick/buttons on the OLED Bonnet for interaction. Your daughter would love this one.

---

## Learning Paths

### Path 1: "I've Never Done Hardware Before"
1. Blink an LED on the Pico (MicroPython basics)
2. Button + LED on the Pico (input/output)
3. Sensor reading with the sensor kit (analog input)
4. OLED display output (I2C communication)
5. Reaction time game (putting it all together)

### Path 2: "I Want to Build Robots"
1. Servo control on Pico (motor basics)
2. Ultrasonic distance sensor (sensing the world)
3. Line-following robot (sensor + motor)
4. Remote-control car via Wi-Fi (Pico 2WH networking)
5. Obstacle-avoiding bot (autonomous behavior)

### Path 3: "I Want to Do AI Stuff"
1. Camera Module 3 setup + photo capture
2. Face detection with OpenCV
3. Object detection with AI HAT+ (on-device)
4. CHARLI Vision integration (camera + voice)
5. Gesture recognition (real-time AI)

### Path 4: "I Want to Explore Space"
1. ISS Tracker on OLED display
2. Weather station with data logging
3. Star tracker with camera
4. Rocket telemetry logger in a model rocket
5. Satellite ground station (receive real signals from space)

### Path 5: "My Daughter Wants to Build Something Cool"
1. Simon Says game (immediate fun, teaches basics)
2. LED pixel art (creative + visual)
3. Digital pet on OLED Bonnet (ongoing engagement)
4. Plant watering system (responsibility + tech)
5. Reaction time game (competition + bragging rights)

---

> **The best project is the one you'll actually finish.** Start small, get something working, then iterate. Every blinking LED is a win.
