import flet as ft

def main(page: ft.Page):
    page.title = "Flet 示例"
    page.window.width = 400
    page.window.height = 300
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def button_click(e):
        text.value = "按钮被点击了！"
        page.update()

    text = ft.Text("欢迎使用 Flet")
    button = ft.Button("点我", on_click=button_click)   # 改成 Button

    page.add(text, button)

ft.run(main)