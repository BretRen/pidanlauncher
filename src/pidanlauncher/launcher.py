from typing import Any
import minecraft_launcher_lib
import subprocess
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from minecraft_launcher_lib.types import MinecraftOptions
from minecraft_launcher_lib.microsoft_types import CompleteLoginResponse

class CallbackHandler(BaseHTTPRequestHandler):
    auth_code: str | None = None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if "code" in params:
            CallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h1>Your all set! Now you can close this page</h1>".encode())
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass

class MinecraftLauncher:
    def __init__(
        self,
        client_id: str,
        redirect_url: str = "http://localhost:31234",
        minecraft_directory: str | None = None,
    ):
        self.client_id = client_id
        self.redirect_url = redirect_url
        self.minecraft_directory = minecraft_directory or str(
            minecraft_launcher_lib.utils.get_minecraft_directory()
        )
        self.version: str = ""
        self.login_data: CompleteLoginResponse | None = None

    def install(self, version: str | None = None) -> str:
        if version is None:
            version = minecraft_launcher_lib.utils.get_latest_version()["release"]
        self.version = version
        minecraft_launcher_lib.install.install_minecraft_version(  # type: ignore
            version, self.minecraft_directory
        )
        return version

    def _get_auth_code(self, login_url: str) -> str:
        port = int(self.redirect_url.split(":")[-1])
        server = HTTPServer(("localhost", port), CallbackHandler)
        CallbackHandler.auth_code = None
        webbrowser.open(login_url)
        print("Waiting for login return...")
        while CallbackHandler.auth_code is None:
            server.handle_request()
        server.server_close()
        assert CallbackHandler.auth_code is not None
        return CallbackHandler.auth_code

    def login(self) -> CompleteLoginResponse:
        login_url, _state, code_verifier = (
            minecraft_launcher_lib.microsoft_account.get_secure_login_data(
                self.client_id, self.redirect_url
            )
        )
        auth_code = self._get_auth_code(login_url)
        self.login_data = minecraft_launcher_lib.microsoft_account.complete_login(
            self.client_id, None, self.redirect_url, auth_code, code_verifier
        )
        return self.login_data

    def get_options(self) -> MinecraftOptions:
        if not self.login_data:
            raise RuntimeError("Use login() first!")
        return {
            "username": self.login_data["name"],
            "uuid": self.login_data["id"],
            "token": self.login_data["access_token"],
        }

    def launch(self, version: str | None = None) -> None:
        if version:
            self.version = version
        if not self.version:
            raise RuntimeError("Please call install() or specify a version first.")
        options = self.get_options()
        command = minecraft_launcher_lib.command.get_minecraft_command(  # type: ignore
            self.version, self.minecraft_directory, options
        )
        subprocess.run(command, cwd=self.minecraft_directory)

    def run(self, version: str | None = None) -> None:
        self.install(version)
        self.login()
        self.launch()

if __name__ == "__main__":
    launcher = MinecraftLauncher(
        client_id="496b4e7d-7115-4ffb-bdb9-04108320023d",
        redirect_url="http://localhost:31234",
    )
    launcher.run()