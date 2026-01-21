import sys
import subprocess
import urllib.request
import shlex

from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QPlainTextEdit,
    QRadioButton, QButtonGroup, QMessageBox,
    QCheckBox, QComboBox, QStackedWidget
)
from PySide6.QtCore import QProcess
from PySide6.QtGui import QIcon


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

def resource_path(*parts: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve().joinpath(*parts)
    return Path(__file__).resolve().parent.parent.joinpath(*parts)


BASE_DIR = base_dir()
ICON_PATH = resource_path("assets", "icon.ico")
DOWNLOADS = BASE_DIR / "downloads"
YTDLP = BASE_DIR / "tools" / "yt-dlp.exe"
YT_DLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"


# check if YTDLP(ytdlp_path) exists, ytdlp_path = YTDLP
def ensure_ytdlp(ytdlp_path: Path):
    if ytdlp_path.exists():
        return
    
    # user agreement check
    msg = QMessageBox()
    msg.setWindowTitle("ALERTA!")
    msg.setIcon(QMessageBox.Question)

    msg.setText(
        "yt-dlp is not found in the required location!\n\n" 
        "This program needs yt-dlp to work,\n" 
        "it'll be downloaded from official yt-dlp GitHub release!"
    )

    btn_yes = msg.addButton("YES YES YES", QMessageBox.YesRole)
    btn_no = msg.addButton("NEIN NEIN NEIN NEIN", QMessageBox.NoRole)

    msg.setDefaultButton(btn_yes)
    msg.exec()
    
    # closes window if user declines
    if msg.clickedButton() is not btn_yes:
        return
    
    # ensure parent directory exists
    ytdlp_path.parent.mkdir(parents=True, exist_ok=True)
    
    # download yt-dlp 
    try:
        urllib.request.urlretrieve(YT_DLP_URL, ytdlp_path)
    except Exception as e:
        QMessageBox.critical(
            None,
            "Download Error",
            f"Failed to download yt-dlp:\n{e}"
        )
        return

    # final confirmation
    if not ytdlp_path.exists():
        QMessageBox.critical(
            None,
            "Download failed",
            "yt-dlp download did not complete correctly."
        )
        return

    # download complete!
    msg = QMessageBox()
    msg.setWindowTitle("Completed!")
    msg.setIcon(QMessageBox.Information)
    msg.setText("yt-dlp has been downloaded successfully!")

    btn_ok = msg.addButton("YAS", QMessageBox.AcceptRole)
    msg.setDefaultButton(btn_ok)

    msg.exec()

# basic download commdns
def build_cmd(
    mode: str,
    url: str,
    *,
    no_playlist: bool,
    video_container: str,
    audio_format: str,
    out_dir: Path,
    extra_args: list[str],
) -> list[str]:
    cmd = [str(YTDLP)]

    # playlist toggle
    if no_playlist:
        cmd += ["--no-playlist"]

    # output template
    cmd += ["-o", str(out_dir / "%(title)s.%(ext)s")]

    if mode == "video":
        # container format
        if video_container == "mp4":
            cmd += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"]
        elif video_container == "mkv":
            cmd += ["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mkv"]
        elif video_container == "webm":
            cmd += ["-f", "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]"]
        else:
            raise ValueError("Invalid video_container")

    elif mode == "audio":
        # audio format
        if audio_format == "mp3":
            cmd += ["-f", "bestaudio", "--extract-audio", "--audio-format", "mp3"]
        elif audio_format == "m4a":
            cmd += ["-f", "bestaudio[ext=m4a]/bestaudio", "--remux-video", "m4a"]
        elif audio_format == "opus":
            cmd += ["-f", "bestaudio", "--extract-audio", "--audio-format", "opus"]
        else:
            raise ValueError("Invalid audio_format")
    else:
        raise ValueError("Invalid mode")

    # extra user args
    cmd += extra_args

    cmd += [url]
    return cmd

def parse_extra_args(extra: str) -> list[str]:
    """
    '--embed-thumbnail --write-subs -S "res:1080"' -> ["--embed-thumbnail", "--write-subs", "-S", "res:1080"]
    """
    extra = (extra or "").strip()
    if not extra:
        return []
    try:
        return shlex.split(extra, posix=False)
    except Exception:
        # fallback: split by spaces only
        return extra.split()

# GUI application
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.setWindowTitle("easy-yt-dlp (with cute cat)")
        self.resize(820, 520)

        self.proc: QProcess | None = None

        layout = QVBoxLayout(self)

        # URL
        layout.addWidget(QLabel("URL"))
        self.url = QLineEdit()
        self.url.setPlaceholderText("Paste your video url here!")
        layout.addWidget(self.url)

        # mode row (1)
        mode_row = QHBoxLayout()
        
        self.rb_video = QRadioButton("Video")
        self.rb_audio = QRadioButton("Audio")
        self.rb_video.setChecked(True)
        
        self.cb_no_playlist = QCheckBox("No Playlist")
        self.cb_no_playlist.setChecked(True)

        group = QButtonGroup(self)
        group.addButton(self.rb_video)
        group.addButton(self.rb_audio)

        self.rb_video.toggled.connect(self.on_mode_changed)

        mode_row.addWidget(self.rb_video)
        mode_row.addWidget(self.rb_audio)
        mode_row.addStretch(1)
        mode_row.addWidget(self.cb_no_playlist)
        
        layout.addLayout(mode_row)
        
        # common row (2)
        common_row = QHBoxLayout()
        common_row.setContentsMargins(9, 0, 0, 0)

        common_row.addWidget(QLabel("Download Location:"))
        self.le_outdir = QLineEdit(str(DOWNLOADS))
        self.le_outdir.setReadOnly(True)
        common_row.addWidget(self.le_outdir, 1)

        self.btn_open_dir = QPushButton("Open Folder")
        self.btn_open_dir.clicked.connect(self.open_download_folder)
        common_row.addWidget(self.btn_open_dir)

        common_row.addStretch(1)
        
        layout.addLayout(common_row)

        # format row (3)
        self.stack = QStackedWidget()
        self.page_video = QWidget()
        self.page_audio = QWidget()

        # video page
        v_layout = QHBoxLayout(self.page_video)
        v_layout.addWidget(QLabel("Format:"))
        self.cmb_video_container = QComboBox()
        self.cmb_video_container.setFixedWidth(90)
        self.cmb_video_container.addItems(["mp4", "mkv", "webm"])
        v_layout.addWidget(self.cmb_video_container)
        v_layout.addStretch(1)

        # audio page
        a_layout = QHBoxLayout(self.page_audio)
        a_layout.addWidget(QLabel("Format:"))
        self.cmb_audio_format = QComboBox()
        self.cmb_audio_format.setFixedWidth(90)
        self.cmb_audio_format.addItems(["mp3", "m4a", "opus"])
        a_layout.addWidget(self.cmb_audio_format)
        a_layout.addStretch(1)

        self.stack.addWidget(self.page_video)  # index 0
        self.stack.addWidget(self.page_audio)  # index 1
        layout.addWidget(self.stack)

        # adv row (4)
        adv_row = QHBoxLayout()
        adv_row.setContentsMargins(9, 0, 0, 0) 
        
        adv_row.addWidget(QLabel("Extra args:"))
        self.le_extra = QLineEdit()
        self.le_extra.setPlaceholderText('For people who used to yt-dlp only!  e.g. --embed-thumbnail --write-subs -S "res:1080"')
        adv_row.addWidget(self.le_extra, 1)

        self.btn_help = QPushButton("Sample args")
        self.btn_help.clicked.connect(self.show_examples)
        adv_row.addWidget(self.btn_help)

        layout.addLayout(adv_row)

        # start/stop
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.stop)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        # log
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log, 1)

        self.on_mode_changed()  # initialize stack

    def on_mode_changed(self):
        # video = 0, audio = 1
        self.stack.setCurrentIndex(0 if self.rb_video.isChecked() else 1)

    def show_examples(self):
        QMessageBox.information(
            self,
            "extra args examples",
            "1) subtitle(when its possible):\n"
            "   --write-subs --sub-langs all,-live_chat\n\n"
            "2) thumbnail/metadata included (useful for audio):\n"
            "   --embed-thumbnail --add-metadata\n\n"
            "3) include uploader in filename:\n"
            "   -o \"%(uploader)s - %(title)s.%(ext)s\"\n\n"
            "4) 1080p prefer(when its available):\n"
            "   -S \"res:1080\""
        )

    def open_download_folder(self):
        DOWNLOADS.mkdir(exist_ok=True)
        try:
            # Windows
            if sys.platform.startswith("win"):
                subprocess.run(["explorer", str(DOWNLOADS)], check=False)
            # macOS
            elif sys.platform == "darwin":
                subprocess.run(["open", str(DOWNLOADS)], check=False)
            # Linux
            else:
                subprocess.run(["xdg-open", str(DOWNLOADS)], check=False)
        except Exception as e:
            QMessageBox.warning(self, "Open folder failed", str(e))

    def append_log(self, text: str):
        self.log.appendPlainText(text.rstrip())

    def start(self):
        url = self.url.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a URL.")
            return

        DOWNLOADS.mkdir(exist_ok=True)

        if not YTDLP.exists():
            QMessageBox.critical(self, "bro theres no yt-dlp", f"theres no yt dlp in this location:\n{YTDLP}")
            return

        mode = "video" if self.rb_video.isChecked() else "audio"

        extra_args = parse_extra_args(self.le_extra.text())

        try:
            cmd = build_cmd(
                mode,
                url,
                no_playlist=self.cb_no_playlist.isChecked(),
                video_container=self.cmb_video_container.currentText(),
                audio_format=self.cmb_audio_format.currentText(),
                out_dir=DOWNLOADS,
                extra_args=extra_args,
            )
        except Exception as e:
            QMessageBox.critical(self, "Option Error", f"Failed to build command:\n{e}")
            return

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
    app.setWindowIcon(QIcon(str(ICON_PATH)))
    
    w = App()
    if not ensure_ytdlp(YTDLP):
        # yt-dlp not available, exit
        pass

    w.show()
    sys.exit(app.exec())