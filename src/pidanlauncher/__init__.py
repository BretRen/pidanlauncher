import threading

import flet as ft
from pidanlauncher.launcher import MinecraftLauncher

TERMS_TEXT = """
Terms of Use

1. This launcher is not affiliated with Mojang; please do not associate it with them.
2. Please use the launcher in a reasonable and lawful manner.
3. By using this launcher, you agree to abide by the relevant terms set by Mojang.
4. The developer is not liable for any losses resulting from the use of this launcher.
5. The launcher is free to use and open-source under the GPL license.

Press [Agree] to continue
"""

launcher = MinecraftLauncher(
    client_id="496b4e7d-7115-4ffb-bdb9-04108320023d",
    redirect_url="http://localhost:31234",
)

async def main(page: ft.Page):
    page.title = "Pidan Launcher"
    page.window.width = 700
    page.window.height = 500
    page.window.min_width = 700
    page.window.min_height = 500
    page.window.max_width = 700
    page.window.max_height = 500
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.resizable = False
    page.window.maximizable = False

    prefs = ft.SharedPreferences()
    has_accepted_terms = await prefs.get("has_accepted_terms") or False

    def show_main():
        def build_account_manage_view():
            initial_text = "Signout" if launcher.is_logged_in else "Login"
            button = ft.Button(content=initial_text)

            def update_button_state():
                if not launcher.is_logged_in:
                    button.content = "Login"
                    button.disabled = False
                    button.on_click = handle_login
                else:
                    button.content = "Signout"
                    button.disabled = False
                    button.on_click = handle_signout

            def handle_login(e: ft.Event[ft.Button]):
                button.disabled = True
                button.content = ft.ProgressRing(width=16, height=16, stroke_width=2)
                button.update()

                def do_login_thread():
                    try:
                        launcher.login()
                    except Exception as e:
                        print(f"Faile to login: {e}")
                    finally:
                        async def update_ui():
                            update_button_state()
                            update_launch_button()
                            page.update()
                        page.run_task(update_ui)
                        
                threading.Thread(target=do_login_thread, daemon=True).start()

            def handle_signout(e: ft.Event[ft.Button]):
                launcher.login_data = None
                update_button_state()
                update_launch_button()

            update_button_state()
            return button

        def on_click_launcher(e: ft.Event[ft.Button]):
            launcher_button.disabled = True
            launcher_button.content = "Starting..."
            page.update()

            def run_and_update():
                try:
                    launcher.run()
                    launcher_button.content = "Launcher Minecraft"
                    launcher_button.disabled = False
                except Exception as e:
                    launcher_button.content = f"Launcher Failed: {e}"
                    launcher_button.disabled = False
                page.update()
            
            threading.Thread(target=run_and_update, daemon=True).start()


        def update_launch_button():
            if launcher.is_logged_in:
                launcher_button.disabled = False
                launcher_button.content = "Launch Minecraft"
            else:
                launcher_button.disabled = True
                launcher_button.content = "You must login"

        launcher_button = ft.Button(on_click=on_click_launcher)
        update_launch_button()

        page.clean()
        page.add(
            ft.Text("Welcome to Pidan Launcher", size=24),
            launcher_button,
            build_account_manage_view(),
        )

    async def disagree(e: ft.Event[ft.Button]):
        await page.window.close()

    async def accept_terms(e: ft.Event[ft.Button]):
        await prefs.set("has_accepted_terms", True)
        show_main()

    def show_terms():
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        terms_card = ft.Container(
            content=ft.Text(TERMS_TEXT, size=14, selectable=True),
            width=520,
            height=280,
            padding=20,
            border=ft.Border.all(1, ft.Colors.GREY_600), # type: ignore
            border_radius=10,
            bgcolor="#252526",
        )

        page.add(
            ft.Column(
                controls=[
                    ft.Text("Terms of Use", size=28, weight=ft.FontWeight.BOLD),
                    terms_card,
                    ft.Row(
                        controls=[
                            ft.Button("Disagree", on_click=disagree),
                            ft.Button("Agree", on_click=accept_terms)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=16,
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            )
        )

    if has_accepted_terms:
        show_main()
    else:
        show_terms()

if __name__ == "__main__":
    ft.run(main)