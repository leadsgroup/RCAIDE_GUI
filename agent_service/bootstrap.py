"""Start and stop the local RCAIDE agent service for desktop development."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


# The desktop development server uses a fixed loopback address so it is not
# exposed to other computers on the network.
LOCAL_SERVICE_URL = "http://127.0.0.1:8765"
_ROOT = Path(__file__).resolve().parents[1]
# This file contains a Windows-encrypted token, never plaintext credentials.
_TOKEN_FILE = _ROOT / ".rcaide-agent-token.dat"


def _service_is_ready(url: str = LOCAL_SERVICE_URL) -> bool:
    """Return True when the configured FastAPI health endpoint responds."""
    try:
        # Keep this timeout short because the check runs during GUI startup.
        with urlopen(f"{url}/health", timeout=0.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload.get("status") == "ok"
    except (URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return False


def _read_windows_encrypted_token(token_file: Path = _TOKEN_FILE) -> str:
    """Decrypt the DPAPI-protected token created by start_ai_demo.ps1."""
    # DPAPI ciphertext can only be decrypted by the Windows user/computer that
    # originally saved it; other platforms must use an environment variable.
    if sys.platform != "win32" or not token_file.exists():
        return ""

    # PowerShell understands the SecureString format written by the launcher.
    script = (
        "$encrypted = (Get-Content -LiteralPath $env:RCAIDE_TOKEN_FILE -Raw).Trim().TrimStart([char]0xFEFF); "
        "$secure = ConvertTo-SecureString $encrypted; "
        "[Net.NetworkCredential]::new('', $secure).Password"
    )
    environment = os.environ.copy()
    # Pass the path through the environment instead of interpolating shell text.
    environment["RCAIDE_TOKEN_FILE"] = str(token_file)
    try:
        # Run invisibly and capture only the decrypted token from stdout.
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            check=True,
            encoding="utf-8",
            errors="replace",
            env=environment,
            timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return completed.stdout.strip()


def start_local_agent_service():
    """Return a spawned backend process, or None when no process is needed."""
    # A centrally hosted service takes priority and needs no local process.
    configured_url = os.getenv("RCAIDE_AGENT_SERVICE_URL", "").strip().rstrip("/")
    if configured_url:
        if "127.0.0.1" not in configured_url and "localhost" not in configured_url:
            return None
        # Reuse a local backend that is already healthy.
        if _service_is_ready(configured_url):
            return None
        # Discard a stale local URL inherited from an old VS Code terminal.
        os.environ.pop("RCAIDE_AGENT_SERVICE_URL", None)
    # Detect a backend started outside this process, such as from PowerShell.
    if _service_is_ready():
        os.environ["RCAIDE_AGENT_SERVICE_URL"] = LOCAL_SERVICE_URL
        return None

    # Prefer a temporary environment token, then fall back to encrypted storage.
    token = os.getenv("GITHUB_MODELS_TOKEN", "").strip()
    if not token:
        token = _read_windows_encrypted_token()
    if not token:
        # Preserve a specific explanation for the assistant error card.
        if _TOKEN_FILE.exists():
            os.environ["RCAIDE_AGENT_STARTUP_ERROR"] = (
                "A saved GitHub Models token exists but cannot be decrypted by this "
                "Windows account or PC. Run START_RCAIDE_AI.cmd and paste the token "
                "again on this computer, then Run main.py normally."
            )
        else:
            os.environ["RCAIDE_AGENT_STARTUP_ERROR"] = (
                "No saved GitHub Models token was found. Run START_RCAIDE_AI.cmd once "
                "to save the token, then Run main.py normally."
            )
        return None

    # Give the child process its own environment containing the backend secret.
    # The token is not written into the GUI, source files, or request payload.
    environment = os.environ.copy()
    environment["GITHUB_MODELS_TOKEN"] = token
    environment.setdefault("RCAIDE_GITHUB_MODEL", "openai/gpt-4.1-mini")
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        # Launch Uvicorn with the same Python interpreter as the desktop app.
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "agent_server.app:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8765",
            ],
            cwd=str(_ROOT),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
    except OSError as exc:
        os.environ["RCAIDE_AGENT_STARTUP_ERROR"] = f"Could not start the AI service: {exc}"
        return None

    # Poll for roughly six seconds so main.py does not race the API startup.
    for _attempt in range(30):
        if process.poll() is not None:
            break
        if _service_is_ready():
            os.environ["RCAIDE_AGENT_SERVICE_URL"] = LOCAL_SERVICE_URL
            os.environ.pop("RCAIDE_AGENT_STARTUP_ERROR", None)
            return process
        time.sleep(0.2)

    # Clean up a process that started but never became ready.
    stop_local_agent_service(process)
    os.environ["RCAIDE_AGENT_STARTUP_ERROR"] = (
        "The local RCAIDE AI service did not become ready."
    )
    return None


def stop_local_agent_service(process) -> None:
    """Stop only the backend process spawned by this desktop session."""
    if process is None or process.poll() is not None:
        return
    # Give Uvicorn a chance to shut down normally before forcing termination.
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)
