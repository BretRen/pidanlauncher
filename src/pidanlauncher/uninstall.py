import asyncio
import os
import shutil
import subprocess
import sys
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

# WHY IT SO HARD!!!!!!!!!!!!!!! Thanks Gemini 4 and Grok save my life
def setup_uninstaller(
    page: ft.Page,
    prefs: ft.SharedPreferences | None = None,
    countdown_seconds: int = 10,
) -> None:
    is_counting_down: bool = False
    txt = ft.Text("", color=ft.Colors.RED_900, weight=ft.FontWeight.W_500, size=13)

    def cancel_uninstall(_: object = None) -> None:
        nonlocal is_counting_down
        is_counting_down = False
        banner.visible = False
        page.update()

    banner = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_400, size=20),
                        ft.Container(content=txt, expand=True),
                    ],
                ),
            ],
            tight=True,
            spacing=8,
        ),
        bgcolor=ft.Colors.RED_50,
        border=ft.Border.all(1, ft.Colors.RED_200),
        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        border_radius=14,
        margin=20,
        visible=False,
    )
    page.overlay.append(banner)

    async def run_countdown() -> None:
        nonlocal is_counting_down
        steps = countdown_seconds * 10
        for i in range(steps + 1):
            if not is_counting_down:
                return
            remaining = countdown_seconds - (i / 10)
            txt.value = f"Continue waiting for {remaining:.0f} seconds, then delete and uninstall all data\n(Press esc to cancel)"
            page.update()
            await asyncio.sleep(0.1)

        if is_counting_down:
            txt.value = "Deleting & Uninstalling...."
            page.update()
            await perform_uninstall(page, prefs)

    def on_key(e: ft.KeyboardEvent) -> None:
        nonlocal is_counting_down
        if is_counting_down and e.key == "Escape":
            cancel_uninstall()
        elif not is_counting_down and e.ctrl and e.shift and e.alt and e.key.upper() == "U":
            is_counting_down = True
            banner.visible = True
            page.run_task(run_countdown)

    page.on_keyboard_event = on_key