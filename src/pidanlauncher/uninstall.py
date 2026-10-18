import asyncio
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import flet as ft

def get_data_dirs() -> list[Path]:
    home = Path.home()
    if sys.platform == "win32":
        base = Path(os.getenv("APPDATA", home / "AppData"/ "Roaming"))
        # In dev, flet is the dir name
        return [base / "Pdnode" / "PidanLauncher", base / "Appveyor Systems Inc" / "flet",]
    elif sys.platform == "darwin":  # macOS
        base = home / "Library" / "Application Support"
        return [base / "com.pdnode.pidanlauncher", base / "flet"]
    else:  # Linux
        base = Path(os.getenv("XDG_DATA_HOME", home / ".local" / "share"))
        return [base / "pidanlauncher", base / "flet"]


def delete_self_executable():
    if not getattr(sys, "frozen", False):
        return

    exe_path = sys.executable

    if sys.platform == "win32":
        subprocess.Popen(
            f'cmd /c ping 127.0.0.1 -n 3 > nul & del /f /q "{exe_path}"', # JUST DELETE lol
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    else:
        # Linux / macOS 允许直接删除或延迟移除
        subprocess.Popen(["sh", "-c", f'sleep 2 && rm -rf "{exe_path}"'])

async def perform_uninstall(page: ft.Page, prefs: ft.SharedPreferences | None = None):
    try:
        target_prefs = prefs or ft.SharedPreferences()
        await target_prefs.clear()
    except Exception:
        pass # eeee TODO: do something

    for folder in get_data_dirs():
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True) # BYE Bye

    delete_self_executable()


    await asyncio.sleep(0.3)
    await page.window.close()

# WHY IT SO HARD!!!!!!!!!!!!!!!
def setup_uninstaller(
    page: ft.Page,
    prefs: ft.SharedPreferences | None = None,
    hold_seconds: float = 10.0,
):
    uninstall_bar = ft.ProgressBar(value=0, color=ft.Colors.RED_400, bgcolor=ft.Colors.RED_900)
    uninstall_text = ft.Text("", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=14)

    banner_card = ft.Container(
        content=ft.Column(
            [uninstall_text, uninstall_bar],
            tight=True,
            spacing=8,
        ),
        bgcolor=ft.Colors.RED_700,
        padding=15,
        border_radius=10,
        margin=20,
        visible=False,
    )
    page.overlay.append(banner_card)

    press_start_time: float = 0.0
    last_event_time: float = 0.0

    def _on_keyboard(e: ft.KeyboardEvent):
        nonlocal press_start_time, last_event_time

        if e.ctrl and e.shift and e.key.upper() == "U":
            now = time.monotonic()
            if press_start_time == 0.0 or (now - last_event_time > 0.8):
                press_start_time = now
            last_event_time = now

    page.on_keyboard_event = _on_keyboard

    async def _watchdog():
        nonlocal press_start_time
        while True:
            now = time.monotonic()

            if press_start_time == 0.0:
                await asyncio.sleep(0.1)
                continue

            # 按键中断超过 0.8 秒 → 重置
            if now - last_event_time > 0.8:
                press_start_time = 0.0
                banner_card.visible = False
                page.update()
                await asyncio.sleep(0.1)
                continue

            # 正在持续按住
            elapsed = now - press_start_time
            remaining = max(0.0, hold_seconds - elapsed)

            banner_card.visible = True
            uninstall_bar.value = min(1.0, elapsed / hold_seconds)
            uninstall_text.value = (
                f"Keep holding Ctrl+Shift+U to uninstall "
                f"({remaining:.1f}s left)"
            )
            page.update()

            if elapsed >= hold_seconds:
                uninstall_text.value = "Deleting..."
                page.update()
                await perform_uninstall(page, prefs)
                break

            await asyncio.sleep(0.1)

    page.run_task(_watchdog)