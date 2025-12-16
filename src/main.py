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

def build_cmd(mode: str, url:str) -> list[str]:
    if mode == "video":
        return [
            str(YTDLP),
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "--no-playlist",
            "-o", str(DOWNLOADS / "%(title)s.%(ext)s"),
            url
        ]
    elif mode == "audio":
        return [
            str(YTDLP),
            "-f", "bestaudio",
            "--extract-audio",
            "--audio-format", "mp3",
            "--no-playlist",
            "-o", str(DOWNLOADS / "%(title)s.%(ext)s"),
            url
        ]
    else:
        raise ValueError("Invalid mode")

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("yt-dlp (mp4/mp3) simpol UI")
        self.resize(820, 460)

        self.proc: QProcess | None = None

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("URL"))
        self.url = QLineEdit()
        self.url.setPlaceholderText("paste yo video url here")
        layout.addWidget(self.url)

        mode_row = QHBoxLayout()
        self.rb_video = QRadioButton("video(mp4)")
        self.rb_mp3 = QRadioButton("mp3")
        self.rb_video.setChecked(True)

        group = QButtonGroup(self)
        group.addButton(self.rb_video)
        group.addButton(self.rb_mp3)

        mode_row.addWidget(self.rb_video)
        mode_row.addWidget(self.rb_mp3)
        mode_row.addStretch(1)
        layout.addLayout(mode_row)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("start")
        self.btn_stop = QPushButton("stop")
        self.btn_stop.setEnabled(False)
        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.stop)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log, 1)

        if not YTDLP.exists():
            QMessageBox.critical(
                self,
                "bro theres no yt-dlp",
                f"theres no yt dlp in this location:\n{YTDLP}",
            )
            self.btn_start.setEnabled(False)

    def append_log(self, text: str):
        self.log.appendPlainText(text.rstrip())

    def start(self):
        url = self.url.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a URL.")
            return

        if not YTDLP.exists():
            QMessageBox.critical(
                self,
                "bro theres no yt-dlp",
                f"theres no yt dlp in this location:\n{YTDLP}",
            )
            return

        mode = "video" if self.rb_video.isChecked() else "audio"
        cmd = build_cmd(mode, url)

        self.append_log("Command:")
        self.append_log(" ".join(cmd))
        self.append_log("")

        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self.on_read)
        self.proc.finished.connect(self.on_finished)

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self.proc.start(cmd[0], cmd[1:])

    def stop(self):
        if self.proc and self.proc.state() != QProcess.NotRunning:
            self.append_log("[INFO] stopping process...")
            self.proc.kill()

    def on_read(self):
        if not self.proc:
            return
        data = (
            self.proc.readAllStandardOutput()
            .data()
            .decode("utf-8", errors="replace")
        )
        self.append_log(data)

    def on_finished(self):
        self.append_log("\n[DONE] done")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = App()
    w.show()
    sys.exit(app.exec())