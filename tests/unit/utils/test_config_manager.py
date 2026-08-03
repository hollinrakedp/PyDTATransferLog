import os
import configparser
from utils.config_manager import ConfigManager


def test_loads_media_and_transfer_types(tmp_path):
    cfg_path = tmp_path / "config.ini"
    cfg = configparser.ConfigParser()
    cfg["UI"] = {
        "MediaTypes": "Flash,SSD",
        "TransferTypes": "Low to High:L2H,High to Low:H2L"
    }
    with open(cfg_path, "w", encoding="utf-8") as fh:
        cfg.write(fh)

    cm = ConfigManager(str(cfg_path))
    media = cm.get_media_types()
    transfers = cm.get_transfer_types()
    assert "Flash" in media and "SSD" in media
    assert transfers.get("Low to High") == "L2H"
    assert transfers.get("High to Low") == "H2L"


def test_reload_returns_true_on_success(tmp_path):
    cfg_path = tmp_path / "config.ini"
    cfg_path.write_text("[UI]\nMediaTypes=Flash\n", encoding="utf-8")
    cm = ConfigManager(str(cfg_path))
    assert cm.reload() is True


def test_get_list_parses_comma_values(tmp_path):
    cfg_path = tmp_path / "config.ini"
    cfg_path.write_text("[UI]\nMediaTypes=Flash, SSD\n", encoding="utf-8")
    cm = ConfigManager(str(cfg_path))
    parsed = cm.get_list("UI", "MediaTypes")
    assert parsed == ["Flash", "SSD"]
