import sys
import subprocess
from pathlib import Path
from PySide6.QtWidgets import(
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QPlainTextEdit,
    QRadioButton, QButtonGroup, QMessageBox 
)
from PySide6.QtCore import QProcess

def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = base_dir()
YTDLP = BASE_DIR / "tools" / "yt-dlp.exe"
DOWNLOADS = BASE_DIR / "downloads"
DOWNLOADS.mkdir(exist_ok=True)

if not YTDLP.exists():
    print("theres no yt-dlp at dedicated location!")
    input("Press Enter to quit")
    exit(1)

print("1 HQvid dl")
print("2 mp3 doownlod")
choice = input("Select (1/2): ").strip()

if choice == "1":
    
    url = input("Insert the youtube link: ").strip()
    if not url:
        print("url is not correct")
        exit(1)
        
    cmd = [
        str(YTDLP),
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
        "--no-playlist",
        "-o", str(DOWNLOADS / "%(title)s.%(ext)s"),
        url
    ]
    
elif choice == "2":
    
    url = input("Insert the youtube link: ").strip()
    if not url:
        print("url is not correct")
        exit(1)
        
    cmd = [
        str(YTDLP),
        "-f", "bestaudio",
        "--extract-audio",
        "--audio-format", "mp3",
        "--no-playlist",
        "-o", str(DOWNLOADS / "%(title)s.%(ext)s"),
        url
    ]
    
else:
    
    print("wrong choice")
    exit(1)

print("\nCommand:")
print(" ".join(cmd))
print()

subprocess.run(cmd)

print("\n Done!")
input("Press enter to quit")
