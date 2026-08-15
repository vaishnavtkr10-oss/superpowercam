🪄 INTERACTIVE WEBCAM BASED SUPERPOWER GAME
> \*\*See Your Power. Unleash It.\*\*
interactive webcam-based superpower game built for the Magic & Superpower . It transforms a normal webcam into a futuristic mirror that detects people, scans them, assigns a superpower, tracks their hand, and lets them use that power to attack targets.
✨ Features
👤 Real-time face detection
👥 Multi-person support
🔬 Futuristic superpower scanning
🎲 Random superpower assignment
🗣️ Voice announcements
✋ Real-time hand tracking
🖐️ Open-palm gesture detection
🔥 Fire
💧 Water
🕸️ Web
⚡ Lightning
🔴 Laser
💜 Energy blast
❄️ Ice
🌌 Cosmic effects
🎯 Target-based gameplay
💥 Projectile collision detection
🏆 Score and combo system
⏱️ Timed rounds
🔊 Sound effects
🔄 Continuous player detection
🧙 Superpowers
Power	Effect
🔥 Fire Master	Fire projectile
💧 Water Master	Water stream
🕸️ Web Master	Web projectile
⚡ Lightning Power	Lightning attack
💜 Energy Blast	Energy projectile
🔴 Laser Power	Laser beam
❄️ Ice Master	Ice projectile
🌌 Cosmic Power	Cosmic energy
All effects are digitally simulated. No real fire, lasers, projectiles, chemicals, or dangerous hardware are used.
🛠️ Tech Stack
Python 3.13 — Main application
OpenCV 5.x — Webcam, face detection, graphics and rendering
MediaPipe 1.0.0 — Hand landmark detection
NumPy — Mathematical calculations
Haar Cascade — Face detection
Windows Speech Synthesis — Voice announcements
Windows Sound — Sound effects
🏗️ Architecture
```text
              WEBCAM
                 │
                 ▼
        ┌─────────────────┐
        │     OpenCV      │
        │  Face Detection │
        └────────┬────────┘
                 │
                 ▼
          PERSON DETECTED
                 │
                 ▼
          POWER SCANNING
                 │
                 ▼
         SUPERPOWER ASSIGNED
                 │
        ┌────────┴─────────┐
        │                  │
        ▼                  ▼
   MediaPipe            Voice
 Hand Landmarker      Announcement
        │
        ▼
    OPEN PALM
        │
        ▼
  POWER ACTIVATED
        │
        ▼
   VISUAL EFFECT
        │
        ▼
      TARGET
        │
        ▼
   HIT + SCORE
```
📋 Requirements
Windows PC/laptop
Python 3.13
Webcam
Speakers
`hand\_landmarker.task`
📁 Project Structure
```text
magicmirror/
├── main.py
├── hand\_landmarker.task
└── README.md
```
`hand\_landmarker.task` must be in the same directory as `main.py`.
The project uses the MediaPipe Tasks API and does not depend on the old `mp.solutions.hands` API.
🚀 Installation
1. Create a virtual environment
```bash
python -m venv .venv
```
2. Activate it
PowerShell:
```powershell
.venv\\Scripts\\Activate.ps1
```
3. Install dependencies
```bash
pip install opencv-python mediapipe numpy
```
4. Add the MediaPipe model
Place the Hand Landmarker model here:
```text
magicmirror/
└── hand\_landmarker.task
```
▶️ Run
```powershell
python main.py
```
🎮 How to Play
Enter the camera — the system detects your face.
Get scanned — the mirror displays `SCANNING AURA...`.
Receive your power — a random power is assigned and announced.
Raise your hand — MediaPipe tracks your hand.
Open your palm — the power is activated.
Attack — the effect launches from your palm toward a target.
Hit targets — successful hits increase score and combo.
Complete the round — reach the target score/hit goal before time expires.
🎯 Controls
Input	Action
`Q`	Quit
`R`	Reset/restart round
🖐️ Open Palm	Fire superpower
🏆 Player State
Each player has an independent state containing:
```text
Player
├── ID
├── Face Position
├── Superpower
├── Score
├── Hits
├── Combo
├── Target
├── Projectiles
└── Timer
```
This allows multiple people to participate in the same camera experience.
🔐 Safety
Magic Mirror is a safe simulation of superpowers.
No real fire
No real lasers
No physical projectiles
No chemicals
No dangerous hardware
All effects are generated digitally using software.
💡 Concept
> \*\*What if a normal mirror could discover your superpower and let you use it?\*\*
Magic Mirror combines computer vision, gesture interaction, animation, audio and game mechanics to turn a simple webcam into an interactive superpower experience.
🔮 Future Improvements
🧑‍🤝‍🧑 Competitive multiplayer
🏆 Global leaderboard
🎭 More superpowers
🕹️ Different game modes
🧠 Advanced gesture recognition
🎥 Body/pose-based powers
🥽 AR/VR support
🎙️ Voice-controlled abilities
🤖 AI-generated power descriptions
📱 Mobile/AR version
🪞 Physical smart-mirror display(IF NEEDED)
```text
WEBCAM
  +
COMPUTER VISION
  +
HAND TRACKING
  +
VISUAL EFFECTS
  +
GAME LOGIC
  +
AUDIO
  =
🪄 INTERACTIVE WEBCAM GAME 
```
🪄 See Your Power. Unleash It.
