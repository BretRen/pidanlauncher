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
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    prefs = ft.SharedPreferences()
    has_accepted_terms = await prefs.get("has_accepted_terms") or False

    def show_main():
        page.clean()
        page.add(
            ft.Text("Welcome to Pidan Launcher", size=24),
            ft.Button("Launch Minecraft", on_click=lambda e: launcher.run()),
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
                spacing=20.
            )
        )

    if has_accepted_terms:
        show_main()
    else:
        show_terms()

if __name__ == "__main__":
    ft.run(main)