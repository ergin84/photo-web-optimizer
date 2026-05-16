#!/usr/bin/env python3
"""Build a standalone executable of Photo Web Optimizer.

Run on the OS you want to package for (no cross-compilation):
  - Windows  -> dist/PhotoWebOptimizer.exe
  - macOS    -> dist/PhotoWebOptimizer.app
  - Linux    -> dist/PhotoWebOptimizer

Requirements (one-off):
  pip install -r requirements-build.txt
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
ENTRY = ROOT / "photo_optimizer_gui.py"
APP_NAME = "PhotoWebOptimizer"


def ensure_icons() -> tuple[Path, Path]:
    png = ROOT / "icon.png"
    ico = ROOT / "icon.ico"
    if not png.exists() or not ico.exists():
        print("Icone mancanti: le genero con make_icon.py ...")
        subprocess.check_call([sys.executable, str(ROOT / "make_icon.py")])
    return png, ico


def check_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        sys.exit(
            "PyInstaller non installato.\n"
            "Esegui:  pip install -r requirements-build.txt"
        )


def clean() -> None:
    for d in ("build", "dist"):
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p)
    for f in ROOT.glob("*.spec"):
        f.unlink()


def main() -> int:
    check_pyinstaller()
    png, ico = ensure_icons()

    system = platform.system()
    print(f"Build platform: {system}")
    print(f"Entry point:    {ENTRY.name}")

    icon = ico if system == "Windows" else png

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        APP_NAME,
        "--icon",
        str(icon),
        "--collect-submodules",
        "PIL",
        str(ENTRY),
    ]
    if system in ("Windows", "Darwin"):
        args.append("--windowed")

    clean()
    print("\n$ " + " ".join(args) + "\n")
    subprocess.check_call(args, cwd=ROOT)

    print("\nBuild completato. Contenuto di dist/:")
    for p in sorted((ROOT / "dist").iterdir()):
        size = p.stat().st_size if p.is_file() else sum(
            f.stat().st_size for f in p.rglob("*") if f.is_file()
        )
        print(f"  {p.name}   {size / 1024 / 1024:.1f} MB")

    if system == "Darwin":
        print(
            "\nSuggerimento: per distribuire crea un .dmg da dist/"
            f"{APP_NAME}.app (es. `create-dmg`)."
        )
    elif system == "Linux":
        print(
            "\nSuggerimento: per un AppImage piu portabile guarda "
            "https://appimage.org/ o lo strumento `appimage-builder`."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
