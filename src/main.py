import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
YTDLP = BASE_DIR / "tools" / "yt-dlp.exe"
DOWNLOADS = BASE_DIR / "downloads"
DOWNLOADS.mkdir(exist_ok=True)

if not YTDLP.exists():
    print("theres no yt-dlp at dedicated location!")
    input("Press Enter to quit")
    exit(1)

print("1) HQvid dl")
print("2) mp3 doownlod")
choice = input("Select (1/2): ").strip()

url = input("Insert the youtube link: ").strip()
if not url:
    print("url is not correct")
    exit(1)

if choice == "1":
    cmd = [
        str(YTDLP),
        "-f", "bestvideo+bestaudio",
        "-o", str(DOWNLOADS / "%(title)s.%(ext)s"),
        url
    ]
elif choice == "2":
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
