import threading
import json
import flet as ft
from minecraft_launcher_lib.types import MinecraftVersionInfo
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
        self.version: str | None = None
        self.account_text: ft.Text | None = None        

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

        await self.setup_window()
        self.page.update()

        has_accepted_terms = False
        saved_account_str = None
        try:
            has_accepted_terms = await self.prefs.get("has_accepted_terms") or False
            saved_account_str = await self.prefs.get("saved_account")
        except Exception as e:
            print(f"Preferences load skipped on hot reload: {e}")

        
        if isinstance(saved_account_str, str) and self.prefs and self.page:
            prefs = self.prefs
            page = self.page
            try:
                self.launcher.login_data = json.loads(saved_account_str)
                def silent_refresh():
                    err = self.launcher.ensure_login()
                    if err is not None:
                        self.launcher.login_data = None
                        if self.page:
                            self.page.run_task(prefs.remove, "saved_account")

                    else:
                        if self.page:
                            self.page.run_task(prefs.set, "saved_account", json.dumps(self.launcher.login_data))

                    if self.page:
                        async def refresh_ui():
                            self.update_account_button_state()
                            self.update_launch_button()
                            self.update_account_text()
                            page.update()

                            
                        self.page.run_task(refresh_ui)
                threading.Thread(target=silent_refresh, daemon=True).start()
            except Exception as e:
                print(f"Failed to load saved account: {e}")
                self.launcher.login_data = None
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

    def build_version_dropdown(self) -> ft.Dropdown:
        versions: list[MinecraftVersionInfo] = launcher.get_avilable_versions()
        options_list = [
            ft.DropdownOption(
                key=v["id"],
                text=v["id"],
                data=v
            )
            for v in versions
            if v["type"] == "release"
        ]

        def on_version_select(e: ft.Event[ft.Dropdown]):
            self.version = dropdown.value
        
        dropdown = ft.Dropdown(options=options_list, on_select=on_version_select, value=launcher.get_latest_version()["release"])
        
        return dropdown

    def build_account_text(self):
        self.account_text = ft.Text(size=14, color=ft.Colors.GREY_400) # type: ignore
        self.update_account_text()
        return self.account_text

    def update_account_text(self) -> None:
        if self.account_text is None:
            return

        if self.launcher.is_logged_in and self.launcher.login_data:
            name = self.launcher.login_data.get("name", "Unknown")
            self.account_text.value = f"You are logged in as {name}"
            self.account_text.visible = True
        else:
            self.account_text.value = ""
            self.account_text.visible = False

    def show_main(self) -> None:
        """Render the main launcher view."""
        if self.page is None:
            return

        self.launcher_button = ft.Button(on_click=self.handle_launch)
        self.update_launch_button()

        self.page.clean()
        self.page.add(
            ft.Text("Welcome to Pidan Launcher", size=24),
            self.build_account_text(),
            self.launcher_button,
            
            self.build_account_manage_view(),
            self.build_version_dropdown(),
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
            btn_text = "Launch Minecraft"

            try:
                self.launcher.run(version=self.version)
            except Exception as ex:
                btn_text = f"Launch Failed: {ex}"
                print(f"Launch error: {ex}")

            if self.page:
                self.page.update()

            async def update_ui():
                if self.launcher_button:
                    self.launcher_button.content = btn_text
                    self.launcher_button.disabled = False
                if self.page:
                    self.page.update()
            if self.page:
                self.page.run_task(update_ui)

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
                    if self.launcher.is_logged_in and self.prefs:
                        await self.prefs.set("saved_account", json.dumps(self.launcher.login_data))

                    self.update_account_button_state()
                    self.update_launch_button()
                    self.update_account_text() 
                    if self.page:
                        self.page.update()

                if self.page:
                    self.page.run_task(update_ui)

        threading.Thread(target=do_login_thread, daemon=True).start()

    async def handle_signout(self, e: ft.Event[ft.Button]) -> None:
        """Handle clicking the signout button."""
        self.launcher.login_data = None
        if self.prefs:
            await self.prefs.remove("saved_account")
        self.update_account_button_state()
        self.update_launch_button()
        self.update_account_text() 
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