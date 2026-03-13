#!/usr/bin/env python3
"""
CHARLI Home - System Monitor

Reads Pi system metrics (CPU temp, RAM, disk, network) and broadcasts
them via StateManager every 10 seconds. The web UI and TUI display
these in their status bars — like Task Manager for CHARLI.

Uses two sources of data:
  1. psutil — a Python library for system info (cross-platform)
     Think of it like the `os` and `process` modules in Node.js but
     with much more detail about CPU, RAM, disk, and network.
  2. Linux thermal zone — a special file the kernel maintains with
     the CPU temperature (Pi-specific)

This module runs as one of the concurrent tasks in charli_home.py,
alongside the voice pipeline and web server.
"""

import asyncio
import os
import subprocess
import psutil  # pip package for system monitoring (like systeminformation in npm)


# ── Configuration ─────────────────────────────────────────────────────

# How often to collect and broadcast metrics (in seconds).
# 10 seconds is a good balance — frequent enough to feel "live"
# but not so frequent that it wastes CPU cycles.
BROADCAST_INTERVAL = 10


# =====================================================================
# METRIC COLLECTION FUNCTIONS
# =====================================================================

def get_cpu_temp() -> float:
    """
    Read CPU temperature from the Pi's thermal zone file.
    Returns temperature in Celsius (e.g., 42.5), or -1 if unavailable.

    How this works:
      The Linux kernel maintains a virtual file at:
        /sys/class/thermal/thermal_zone0/temp
      This file contains the CPU temperature in MILLIDEGREES.
      So "42000" in the file means 42.0°C.

      It's not a real file on disk — it's a "virtual filesystem" that
      the kernel generates on-the-fly. Reading it is like calling a
      system API, but through the filesystem interface. This is a
      common pattern in Linux (everything is a file!).

      This file only exists on systems with thermal sensors (like the Pi).
      On a Mac or regular Linux PC, it might not exist — that's why we
      handle FileNotFoundError gracefully.
    """
    thermal_path = "/sys/class/thermal/thermal_zone0/temp"
    try:
        with open(thermal_path, "r") as f:
            # Read the file, strip whitespace, convert to int, divide by 1000
            # Example: "42500\n" → 42500 → 42.5
            return round(int(f.read().strip()) / 1000, 1)
    except (FileNotFoundError, ValueError):
        # Not on a Pi, or thermal zone not available
        return -1


def get_tailscale_status() -> str:
    """
    Check if Tailscale VPN is connected.
    Returns "connected", "disconnected", "not_installed", or "timeout".

    Tailscale is the private network that connects the Pi to the Mac Mini.
    If it's not connected, the Pi can't reach CHARLI's brain (OpenClaw).

    We check by running `tailscale status --json` as a subprocess.
    If the command succeeds (return code 0), Tailscale is connected.
    """
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,  # Capture stdout/stderr instead of printing
            text=True,            # Return strings, not bytes
            timeout=5             # Don't hang forever if Tailscale is stuck
        )
        if result.returncode == 0:
            return "connected"
        return "disconnected"
    except FileNotFoundError:
        # `tailscale` command not found — not installed
        return "not_installed"
    except subprocess.TimeoutExpired:
        # Command took too long (Tailscale might be starting up)
        return "timeout"
    except Exception:
        return "unknown"


def collect_metrics() -> dict:
    """
    Gather all system metrics into a single dictionary.

    Returns something like:
      {
        "cpu_temp": 42.5,
        "cpu_percent": 15.2,
        "ram_total_mb": 8192,
        "ram_used_mb": 1024,
        "ram_percent": 12.5,
        "disk_total_gb": 238.5,
        "disk_used_gb": 12.3,
        "disk_percent": 5.2,
        "tailscale": "connected"
      }

    This dict gets sent to all WebSocket clients (browser UI, TUI)
    and stored on state_manager.system_metrics for the REST API.
    """

    # psutil.virtual_memory() returns a named tuple with:
    #   total, available, percent, used, free, active, inactive, ...
    # Like: const { total, used, percent } = os.totalmem() but richer
    mem = psutil.virtual_memory()

    # psutil.disk_usage("/") returns disk stats for the root filesystem.
    # On the Pi with NVMe SSD: total=256GB, used=~12GB
    disk = psutil.disk_usage("/")

    return {
        # CPU temperature in Celsius (Pi-specific)
        "cpu_temp": get_cpu_temp(),

        # CPU usage as a percentage (0-100).
        # interval=1 means "measure over 1 second" — this is BLOCKING,
        # which is why we run collect_metrics() in run_in_executor().
        "cpu_percent": psutil.cpu_percent(interval=1),

        # RAM stats — total, used, and percentage
        # 1024 * 1024 converts bytes to megabytes
        "ram_total_mb": round(mem.total / (1024 * 1024)),
        "ram_used_mb": round(mem.used / (1024 * 1024)),
        "ram_percent": mem.percent,

        # Disk stats — total, used, and percentage
        # 1024 ** 3 converts bytes to gigabytes (1024^3 = 1 GB)
        "disk_total_gb": round(disk.total / (1024 ** 3), 1),
        "disk_used_gb": round(disk.used / (1024 ** 3), 1),
        "disk_percent": disk.percent,

        # Tailscale VPN status
        "tailscale": get_tailscale_status(),
    }


# =====================================================================
# MONITOR LOOP — Runs forever as an async background task
# =====================================================================

async def monitor_loop(state_manager):
    """
    Async loop that collects and broadcasts system metrics every 10 seconds.

    This runs as one of the concurrent tasks in asyncio.gather():
      await asyncio.gather(
          run_web_server(state),
          voice_pipeline(state),
          monitor_loop(state),      ← this function
          mac_link.run(),
      )

    It collects metrics in a background thread (because cpu_percent blocks),
    stores them on state_manager for the REST API, and broadcasts them
    to all connected WebSocket clients.

    The web UI and TUI use these metrics to show a status bar like:
      CPU: 42°C  |  RAM: 12%  |  NET: connected
    """
    loop = asyncio.get_event_loop()

    while True:
        try:
            # collect_metrics() is BLOCKING (cpu_percent sleeps for 1 second).
            # run_in_executor moves it to a thread so the event loop stays responsive.
            metrics = await loop.run_in_executor(None, collect_metrics)

            # Store metrics on the state manager so the REST API endpoint
            # GET /api/status can include them in its response.
            state_manager.system_metrics = metrics

            # Broadcast to all connected WebSocket clients (browsers, TUI).
            # They receive: {"type": "system", "metrics": {...}}
            await state_manager._broadcast({
                "type": "system",
                "metrics": metrics,
            })

        except asyncio.CancelledError:
            # Graceful shutdown — stop the loop
            break
        except Exception as e:
            # Don't crash the whole system if one metric read fails.
            # Just log it and try again next interval.
            print(f"⚠️ System monitor error: {e}")

        # Wait 10 seconds before collecting again.
        # asyncio.sleep() is non-blocking — it lets other tasks run.
        # This is like: await new Promise(resolve => setTimeout(resolve, 10000))
        await asyncio.sleep(BROADCAST_INTERVAL)


# ── Standalone Test ───────────────────────────────────────────────────
# Run this directly to see your system's metrics:
#   python3 src/system_monitor.py
if __name__ == "__main__":
    import json
    metrics = collect_metrics()
    print(json.dumps(metrics, indent=2))
