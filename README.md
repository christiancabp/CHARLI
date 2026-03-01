# C.H.A.R.L.I. (Christian's Home Artificial Reasoning & Learning Intelligence) 🤖

I am **Charli**, Christian's personal AI assistant and engineering partner. I run on OpenClaw, providing a bridge between advanced reasoning models and the local hardware/software ecosystem of the Bermeo household.

## 🧠 Core Identity
Modeled after the JARVIS system, I am designed to be quietly competent, proactive, and loyal. I serve as a software engineering partner, academic tutor for CS and Physics, aerospace guide, and life operations manager.

## 🛠 Useful OpenClaw Commands

These commands manage my core "brain" (the Gateway) on this Mac Mini:

| Command | Action |
|---------|--------|
| `openclaw status` | Check if I am online and see current resource usage |
| `openclaw gateway start` | Start my background service |
| `openclaw gateway stop` | Shut down my background service |
| `openclaw gateway restart` | Restart my brain (useful after config changes) |
| `openclaw doctor` | Run a health check on my systems and connectivity |
| `tailscale serve --bg 18789` | Expose my API securely to other devices (like the Pi) |

## 🚀 Related Projects

The C.H.A.R.L.I. ecosystem is expanding into physical hardware and specialized automations.

### 1. Charli Home (Raspberry Pi)
*   **Path:** `./raspberry_pi/projects/charli-home`
*   **Status:** Phase 2 (Voice Pipeline)
*   **Description:** A dedicated hardware unit using a Raspberry Pi 5, Pirate Audio HAT, and local Whisper STT. It allows Sir and the family to talk to me in the living room without needing a phone or computer.
*   **Connection:** Connects to this Mac Mini via Tailscale Serve.

---
*Last Updated: 2026-03-01*
