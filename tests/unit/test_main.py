import os
import sys

import pytest

import main


def test_parse_tab_argument_variants(capsys):
    assert main.parse_tab_argument(None) == 0
    assert main.parse_tab_argument("  ") == 0
    assert main.parse_tab_argument("1") == 1
    assert main.parse_tab_argument("review") == 2

    result = main.parse_tab_argument("invalid")
    captured = capsys.readouterr()
    assert "Invalid tab" in captured.out
    assert result == 0


@pytest.mark.gui
def test_check_for_help_request_triggers_gui(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["prog", "--help"])
    monkeypatch.setattr(main, "show_gui_help", lambda: calls.append(True))
    monkeypatch.setattr(main, "is_console_available", lambda: False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    assert main.check_for_help_request() is True
    assert calls == [True]


@pytest.mark.gui
def test_check_for_help_request_passthrough(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--help"])
    monkeypatch.setattr(main, "is_console_available", lambda: True)
    monkeypatch.setattr(sys, "frozen", False, raising=False)

    assert main.check_for_help_request() is False


@pytest.mark.gui
def test_generate_gui_help_content_contains_expected_sections():
    content = main.generate_gui_help_content()
    assert "DTA File Transfer Log" in content
    assert "CLI executable" in content
    assert "--tab" in content


def test_is_console_available_tty(monkeypatch):
    class DummyStdout:
        def isatty(self):
            return True

    monkeypatch.setattr(sys, "platform", "linux", raising=False)
    monkeypatch.setattr(sys, "stdout", DummyStdout())

    assert main.is_console_available() is True


def test_main_runs_cli_transfer_and_restores_cwd(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(sys, "argv", ["prog", "-t"])  # trigger transfer CLI path
    monkeypatch.setattr(main, "run_cli", lambda: calls.append("transfer"))
    monkeypatch.setattr(main, "run_request_cli", lambda: calls.append("request"))

    # Track chdir calls; ensure we restore to original
    chdirs = []
    monkeypatch.setattr(os, "chdir", lambda path: chdirs.append(path))

    original_cwd = os.getcwd()
    main.main()

    assert calls == ["transfer"]
    assert chdirs  # chdir invoked at least once
    assert os.getcwd() == original_cwd  # no lingering cwd change


def test_main_runs_cli_request(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["prog", "--request"])  # trigger request CLI path
    monkeypatch.setattr(main, "run_cli", lambda: calls.append("transfer"))
    monkeypatch.setattr(main, "run_request_cli", lambda: calls.append("request"))
    monkeypatch.setattr(os, "chdir", lambda _path: None)

    main.main()

    assert calls == ["request"]


def test_main_returns_early_on_help(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog"])  # no args
    monkeypatch.setattr(main, "check_for_help_request", lambda: True)

    # If main continued, it would call os.chdir; make that fail to detect unwanted calls
    monkeypatch.setattr(os, "chdir", lambda _path: (_ for _ in ()).throw(AssertionError("chdir should not be called")))

    main.main()


@pytest.mark.gui
def test_main_runs_gui_path_with_dummy_qt(monkeypatch, tmp_path):
    import sys
    from unittest.mock import MagicMock
    
    # Force GUI path (no CLI args, help returns False)
    monkeypatch.setattr(sys, "argv", ["prog"])  # triggers GUI path
    monkeypatch.setattr(main, "check_for_help_request", lambda: False)
    monkeypatch.setattr(sys, "exit", lambda _code=None: None)

    # Replace chdir to avoid touching real CWD
    monkeypatch.setattr(os, "chdir", lambda _path: None)

    # Dummy parser that accepts --tab
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tab")
    monkeypatch.setattr(main, "create_gui_parser", lambda: parser)

    # Dummy ConfigManager
    class DummyConfig:
        def get(self, section, option, fallback=""):
            if section == "UI" and option == "Theme":
                return "fake-theme"
            if section == "UI" and option == "DefaultTab":
                return fallback
            return fallback

    monkeypatch.setattr(main, "ConfigManager", lambda _path: DummyConfig())

    # Dummy QApplication - patch it in PySide6.QtWidgets namespace
    class DummyApp:
        _instance = None

        def __init__(self, *_args, **_kwargs):
            DummyApp._instance = self
            self.styles = []
        @classmethod
        def instance(cls):
            return cls._instance
        def setApplicationName(self, _name):
            pass
        def setOrganizationName(self, _name):
            pass
        def setStyleSheet(self, _sheet):
            self.styles.append(_sheet)
        def exec(self):
            return 0

    # Patch PySide6.QtWidgets module before it's imported
    mock_qtwidgets = MagicMock()
    mock_qtwidgets.QApplication = DummyApp
    sys.modules['PySide6.QtWidgets'] = mock_qtwidgets

    # Dummy app window with tab_widget
    class DummyTabs:
        def __init__(self):
            self.index = None
        def setCurrentIndex(self, idx):
            self.index = idx

    created_windows = []

    class DummyAppWindow:
        def __init__(self, _config):
            self.tab_widget = DummyTabs()
            created_windows.append(self)
        def show(self):
            pass

    # Patch ui.app_window module before it's imported
    mock_app_window = MagicMock()
    mock_app_window.DTATransferLogApp = DummyAppWindow
    sys.modules['ui.app_window'] = mock_app_window

    # Fake theme file existence and contents
    monkeypatch.setattr(os.path, "exists", lambda path: path.endswith("fake-theme.qss"))
    import builtins
    import io
    real_open = builtins.open
    def fake_open(path, *args, **kwargs):
        if path.endswith("fake-theme.qss"):
            return io.StringIO("body")
        return real_open(path, *args, **kwargs)
    monkeypatch.setattr(builtins, "open", fake_open)

    main.main()

    assert isinstance(DummyApp._instance, DummyApp)
    assert created_windows[0].tab_widget.index == 0
    assert DummyApp._instance.styles == ["body"]
