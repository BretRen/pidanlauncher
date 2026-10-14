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


class PidanLauncherApp:
    def __init__(
        self,
        launcher: MinecraftLauncher | None = None,
        terms_text: str = TERMS_TEXT,
    ) -> None:
        self.launcher = launcher or MinecraftLauncher(
            client_id="496b4e7d-7115-4ffb-bdb9-04108320023d",
            redirect_url="http://localhost:31234",
        )
        self.terms_text = terms_text
        self.page: ft.Page | None = None
        self.prefs: ft.SharedPreferences | None = None
        self.launcher_button: ft.Button | None = None
        self.account_button: ft.Button | None = None

    async def setup_window(self) -> None:
        """Configure initial window properties and display settings."""
        if self.page is None:
            return

        # Windows Settings
        ## Because otherwise, the window cannot be displayed at its normal size.
        self.page.window.visible = False

        self.page.title = "Pidan Launcher"
        self.page.window.width = 700
        self.page.window.height = 500
        self.page.window.min_width = 700
        self.page.window.min_height = 500
        self.page.window.max_width = 700
        self.page.window.max_height = 500
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.window.resizable = False
        self.page.window.maximizable = False

        self.page.update()
        await self.page.window.center()

        self.page.window.visible = True
        self.page.update()

    async def start(self, page: ft.Page) -> None:
        """Start the launcher application for the given page."""
        self.page = page
        await self.setup_window()

        self.prefs = ft.SharedPreferences()
        has_accepted_terms = await self.prefs.get("has_accepted_terms") or False

        if has_accepted_terms:
            self.show_main()
        else:
            self.show_terms()

    # --- Terms View ---

    def show_terms(self) -> None:
        """Render the Terms of Use view."""
        if self.page is None:
            return

        self.page.clean()
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        terms_card = ft.Container(
            content=ft.Text(self.terms_text, size=14, selectable=True),
            width=520,
            height=280,
            padding=20,
            border=ft.Border.all(1, ft.Colors.GREY_600),  # type: ignore
            border_radius=10,
            bgcolor="#252526",
        )

        self.page.add(
            ft.Column(
                controls=[
                    ft.Text("Terms of Use", size=28, weight=ft.FontWeight.BOLD),
                    terms_card,
                    ft.Row(
                        controls=[
                            ft.Button("Disagree", on_click=self.handle_disagree),
                            ft.Button("Agree", on_click=self.handle_accept_terms),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=16,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            )
        )

    async def handle_disagree(self, e: ft.Event[ft.Button]) -> None:
        """Handle disagree action by closing the application window."""
        if self.page:
            await self.page.window.close()

    async def handle_accept_terms(self, e: ft.Event[ft.Button]) -> None:
        """Handle agree action by recording preference and displaying main view."""
        if self.prefs:
            await self.prefs.set("has_accepted_terms", True)
        self.show_main()

    # --- Main View ---

    def show_main(self) -> None:
        """Render the main launcher view."""
        if self.page is None:
            return

        self.launcher_button = ft.Button(on_click=self.handle_launch)
        self.update_launch_button()

        self.page.clean()
        self.page.add(
            ft.Text("Welcome to Pidan Launcher", size=24),
            self.launcher_button,
            self.build_account_manage_view(),
        )

    # --- Launcher Control ---

    def update_launch_button(self) -> None:
        """Update the launch button state based on authentication status."""
        if self.launcher_button is None:
            return

        if self.launcher.is_logged_in:
            self.launcher_button.disabled = False
            self.launcher_button.content = "Launch Minecraft"
        else:
            self.launcher_button.disabled = True
            self.launcher_button.content = "You must login"

    def handle_launch(self, e: ft.Event[ft.Button]) -> None:
        """Handle clicking the launch button."""
        if self.launcher_button is None or self.page is None:
            return

        self.launcher_button.disabled = True
        self.launcher_button.content = "Starting..."
        self.page.update()

        def run_and_update():
            try:
                self.launcher.run()
                if self.launcher_button:
                    self.launcher_button.content = "Launcher Minecraft"
                    self.launcher_button.disabled = False
            except Exception as ex:
                if self.launcher_button:
                    self.launcher_button.content = f"Launcher Failed: {ex}"
                    self.launcher_button.disabled = False
            if self.page:
                self.page.update()

        threading.Thread(target=run_and_update, daemon=True).start()

    # --- Account Management ---

    def build_account_manage_view(self) -> ft.Button:
        """Build and return the account management button."""
        initial_text = "Signout" if self.launcher.is_logged_in else "Login"
        self.account_button = ft.Button(content=initial_text)
        self.update_account_button_state()
        return self.account_button

    def update_account_button_state(self) -> None:
        """Update the account button text and callback depending on login status."""
        if self.account_button is None:
            return

        if not self.launcher.is_logged_in:
            self.account_button.content = "Login"
            self.account_button.disabled = False
            self.account_button.on_click = self.handle_login
        else:
            self.account_button.content = "Signout"
            self.account_button.disabled = False
            self.account_button.on_click = self.handle_signout

    def handle_login(self, e: ft.Event[ft.Button]) -> None:
        """Handle clicking the login button."""
        if self.account_button is None or self.page is None:
            return

        self.account_button.disabled = True
        self.account_button.content = ft.ProgressRing(width=16, height=16, stroke_width=2)
        self.account_button.update()

        def do_login_thread():
            try:
                self.launcher.login()
            except Exception as ex:
                print(f"Faile to login: {ex}")
            finally:
                async def update_ui():
                    self.update_account_button_state()
                    self.update_launch_button()
                    if self.page:
                        self.page.update()

                if self.page:
                    self.page.run_task(update_ui)

        threading.Thread(target=do_login_thread, daemon=True).start()

    def handle_signout(self, e: ft.Event[ft.Button]) -> None:
        """Handle clicking the signout button."""
        self.launcher.login_data = None
        self.update_account_button_state()
        self.update_launch_button()
        if self.page:
            self.page.update()


launcher = MinecraftLauncher(
    client_id="496b4e7d-7115-4ffb-bdb9-04108320023d",
    redirect_url="http://localhost:31234",
)


async def main(page: ft.Page):
    app = PidanLauncherApp(launcher=launcher)
    await app.start(page)


if __name__ == "__main__":
    ft.run(main)