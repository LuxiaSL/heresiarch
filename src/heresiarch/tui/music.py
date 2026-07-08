"""Background music playback for the TUI.

Plays the bundled chiptune loop (see scripts/compose_theme.py) via
whatever system player is available — no Python audio dependencies:

    ffplay  — gapless native looping (preferred)
    paplay / aplay — looped by a restart thread (tiny seam gap)

Everything is failure-proof: no backend, no asset, or a dead player
process simply means silence. Music must never take down the game.

Disable autostart with HERESIARCH_NO_MUSIC=1; toggle in-game with M.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
from pathlib import Path

THEME_PATH = Path(__file__).parent / "assets" / "heresiarch_theme.wav"
NO_MUSIC_ENV = "HERESIARCH_NO_MUSIC"


class MusicPlayer:
    """Loops a WAV in the background through a system audio player."""

    def __init__(self, wav_path: Path = THEME_PATH):
        self.wav_path = wav_path
        self._proc: subprocess.Popen | None = None
        self._loop_thread: threading.Thread | None = None
        self._stop_flag = threading.Event()
        self._backend = self._detect_backend()

    @staticmethod
    def _detect_backend() -> str | None:
        for candidate in ("ffplay", "paplay", "aplay"):
            if shutil.which(candidate):
                return candidate
        return None

    @property
    def available(self) -> bool:
        return self._backend is not None and self.wav_path.exists()

    @property
    def playing(self) -> bool:
        if self._proc is not None and self._proc.poll() is None:
            return True
        return bool(self._loop_thread and self._loop_thread.is_alive())

    def start(self) -> bool:
        """Begin looping. Returns True if playback started."""
        if not self.available or self.playing:
            return self.playing
        try:
            if self._backend == "ffplay":
                self._proc = subprocess.Popen(
                    ["ffplay", "-nodisp", "-loglevel", "quiet",
                     "-loop", "0", str(self.wav_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                )
            else:
                self._stop_flag.clear()
                self._loop_thread = threading.Thread(
                    target=self._restart_loop, daemon=True,
                )
                self._loop_thread.start()
            return True
        except OSError:
            self._proc = None
            return False

    def _restart_loop(self) -> None:
        """paplay/aplay have no loop flag — restart until stopped."""
        while not self._stop_flag.is_set():
            try:
                self._proc = subprocess.Popen(
                    [self._backend, str(self.wav_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                )
                self._proc.wait()
            except OSError:
                break

    def stop(self) -> None:
        self._stop_flag.set()
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    proc.kill()
                except OSError:
                    pass
        self._loop_thread = None

    def toggle(self) -> bool:
        """Flip playback. Returns True if now playing."""
        if self.playing:
            self.stop()
            return False
        return self.start()

    @staticmethod
    def autostart_enabled() -> bool:
        return os.environ.get(NO_MUSIC_ENV, "") not in ("1", "true", "yes")
