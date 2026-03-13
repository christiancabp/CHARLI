#!/usr/bin/env python3
"""
CHARLI Home - System Monitor

Reads Pi system metrics (CPU temp, RAM, disk, network) and broadcasts
them via StateManager every 10 seconds. The web UI and TUI display
these in their status bars.

Uses psutil for cross-platform system info + Pi-specific thermal zone
for accurate CPU temperature.
"""

import asyncio
import os
import subprocess
import psutil


# How often to broadcast metrics (seconds)
BROADCAST_INTERVAL = 10


def get_cpu_temp() -> float:
    """
    Read CPU temperature from the Pi's thermal zone.
    Returns temperature in Celsius, or -1 if unavailable.

    On a Pi, the CPU temp lives in a special file maintained by the kernel.
    This is like reading a sensor — the OS updates it automatically.
    """
    thermal_path = "/sys/class/thermal/thermal_zone0/temp"
    try:
        with open(thermal_path, "r") as f:
            # The file contains millidegrees (e.g., 42000 = 42.0°C)
            return round(int(f.read().strip()) / 1000, 1)
    except (FileNotFoundError, ValueError):
        # Not on a Pi, or thermal zone not available
        return -1


def get_tailscale_status() -> str:
    """
    Check if Tailscale is connected by running `tailscale status`.
    Returns "connected", "disconnected", or "not_installed".
    """
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return "connected"
        return "disconnected"
    except FileNotFoundError:
        return "not_installed"
    except subprocess.TimeoutExpired:
        return "timeout"
    except Exception:
        return "unknown"


def collect_metrics() -> dict:
    """
    Gather all system metrics into a single dict.
    This runs in the background every BROADCAST_INTERVAL seconds.
    """
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "cpu_temp": get_cpu_temp(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "ram_total_mb": round(mem.total / (1024 * 1024)),
        "ram_used_mb": round(mem.used / (1024 * 1024)),
        "ram_percent": mem.percent,
        "disk_total_gb": round(disk.total / (1024 ** 3), 1),
        "disk_used_gb": round(disk.used / (1024 ** 3), 1),
        "disk_percent": disk.percent,
        "tailscale": get_tailscale_status(),
    }


async def monitor_loop(state_manager):
    """
    Async loop that collects and broadcasts system metrics.
    Runs as a background task alongside the voice pipeline and web server.

    Stores metrics on state_manager.system_metrics so the REST API
    can also serve them via GET /api/status.
    """
    loop = asyncio.get_event_loop()

    while True:
        try:
            # Run collection in executor since psutil.cpu_percent() blocks
            metrics = await loop.run_in_executor(None, collect_metrics)

            # Store on state manager for REST API access
            state_manager.system_metrics = metrics

            # Broadcast to all WebSocket clients
            await state_manager._broadcast({
                "type": "system",
                "metrics": metrics,
            })

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"⚠️ System monitor error: {e}")

        await asyncio.sleep(BROADCAST_INTERVAL)


if __name__ == "__main__":
    # Quick standalone test — prints metrics once
    import json
    metrics = collect_metrics()
    print(json.dumps(metrics, indent=2))
