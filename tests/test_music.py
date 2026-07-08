"""Tests for the chiptune asset and the music player plumbing."""

import wave

from heresiarch.tui.music import THEME_PATH, MusicPlayer


class TestThemeAsset:
    def test_asset_exists_and_is_sane(self):
        assert THEME_PATH.exists(), "run scripts/compose_theme.py"
        with wave.open(str(THEME_PATH)) as w:
            assert w.getnchannels() == 1
            assert w.getsampwidth() == 2
            assert w.getframerate() == 44100
            duration = w.getnframes() / w.getframerate()
            assert 30 < duration < 40  # 16 bars at 116 BPM


class TestMusicPlayer:
    def test_missing_asset_is_unavailable(self, tmp_path):
        p = MusicPlayer(wav_path=tmp_path / "nope.wav")
        assert p.available is False
        assert p.start() is False   # no crash
        p.stop()                    # no crash

    def test_no_backend_is_unavailable(self, monkeypatch):
        import heresiarch.tui.music as music
        monkeypatch.setattr(music.shutil, "which", lambda _: None)
        p = MusicPlayer()
        assert p.available is False

    def test_toggle_lifecycle_without_audio(self, tmp_path):
        p = MusicPlayer(wav_path=tmp_path / "nope.wav")
        assert p.toggle() is False  # can't start, stays off
        assert p.playing is False

    def test_autostart_env(self, monkeypatch):
        monkeypatch.setenv("HERESIARCH_NO_MUSIC", "1")
        assert MusicPlayer.autostart_enabled() is False
        monkeypatch.delenv("HERESIARCH_NO_MUSIC")
        assert MusicPlayer.autostart_enabled() is True
