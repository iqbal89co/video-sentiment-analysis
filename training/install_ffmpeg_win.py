import os
import sys
import subprocess
import tempfile
import shutil
import zipfile
import platform
from pathlib import Path
from urllib.request import urlretrieve

def _cmd_exists(cmd: str) -> bool:
    from shutil import which
    return which(cmd) is not None

def _verify_ffmpeg() -> bool:
    try:
        out = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        print("FFmpeg found:\n", out.stdout.splitlines()[0])
        return True
    except Exception:
        return False

def _append_to_path(p: Path):
    os.environ["PATH"] = str(p) + os.pathsep + os.environ.get("PATH", "")

def _install_ffmpeg_windows() -> bool:
    # 1) If FFmpeg already on PATH, done.
    if _verify_ffmpeg():
        return True

    # 2) Try winget or choco if available (fast path).
    try:
        if _cmd_exists("winget"):
            # Gyan packages FFmpeg in winget
            subprocess.check_call(["winget", "install", "--id", "Gyan.FFmpeg", "-e", "--source", "winget"])
            return _verify_ffmpeg()
    except Exception:
        pass
    try:
        if _cmd_exists("choco"):
            subprocess.check_call(["choco", "install", "ffmpeg", "-y"])
            return _verify_ffmpeg()
    except Exception:
        pass

    # 3) Fallback: download a prebuilt zip and place ffmpeg.exe under ./bin/ffmpeg
    # Use the "essentials" build from Gyan.dev which is stable for Windows.
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    dest_root = Path(__file__).resolve().parent.parent / "bin" / "ffmpeg"
    dest_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        zip_path = Path(td) / "ffmpeg.zip"
        print(f"Downloading FFmpeg zip from {url} ...")
        urlretrieve(url, zip_path)
        print("Extracting FFmpeg ...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(td)

        # Find ffmpeg.exe (under ffmpeg-*-essentials_build/bin/ffmpeg.exe)
        extracted_root = next(Path(td).glob("ffmpeg-*"))
        exe = extracted_root / "bin" / "ffmpeg.exe"
        if not exe.exists():
            print("Could not locate ffmpeg.exe in the downloaded archive.")
            return False

        # Copy ffmpeg.exe (and optionally dlls) to our local bin
        shutil.copy2(exe, dest_root / "ffmpeg.exe")
        # Also copy accompanying DLLs to the same folder so codecs load
        for dll in (extracted_root / "bin").glob("*.dll"):
            try:
                shutil.copy2(dll, dest_root / dll.name)
            except Exception:
                pass

    _append_to_path(dest_root)
    return _verify_ffmpeg()

def _install_ffmpeg_linux() -> bool:
    if _verify_ffmpeg():
        return True
    # Try apt/yum/apk if present
    for cmd in (["apt-get", "update"], ["apt-get", "install", "-y", "ffmpeg"],
                ["yum", "install", "-y", "ffmpeg"], ["apk", "add", "ffmpeg"]):
        try:
            if _cmd_exists(cmd[0]):
                subprocess.check_call(cmd)
                if _verify_ffmpeg():
                    return True
        except Exception:
            continue
    # Last resort: tell user to install manually
    print("FFmpeg install on Linux failed; please install with your package manager (e.g., apt-get install ffmpeg).")
    return False

def _install_ffmpeg_macos() -> bool:
    if _verify_ffmpeg():
        return True
    # Try Homebrew
    if _cmd_exists("brew"):
        try:
            subprocess.check_call(["brew", "install", "ffmpeg"])
            return _verify_ffmpeg()
        except Exception:
            pass
    print("FFmpeg install on macOS failed; install Homebrew and run: brew install ffmpeg")
    return False

def install_ffmpeg() -> bool:
    """
    Ensures ffmpeg is available on PATH.
    Returns True if ffmpeg is present/installed, False otherwise.
    """
    print("Starting FFmpeg check/installation...")

    # Always ensure pip deps first (your code expected this)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "ffmpeg-python"])
    except Exception:
        # ffmpeg-python is optional helper; ignore failure
        pass

    system = platform.system().lower()
    if "windows" in system:
        ok = _install_ffmpeg_windows()
    elif "linux" in system:
        ok = _install_ffmpeg_linux()
    elif "darwin" in system:
        ok = _install_ffmpeg_macos()
    else:
        print(f"Unsupported OS: {system}. Please install FFmpeg manually and ensure it is on PATH.")
        ok = _verify_ffmpeg()

    if not ok:
        print("FFmpeg is not available. Some audio/video ops will fail.")
    return ok

if __name__ == "__main__":
    sys.exit(0 if install_ffmpeg() else 1)
