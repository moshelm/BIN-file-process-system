import importlib

from process_service.src.utils import config as config_module


def test_config_data_reload_with_monkeypatched_json_loader(monkeypatch):
    monkeypatch.setattr(config_module, "read_json_file", lambda path: {"redis_url": "redis://127.0.0.1:6379"})
    importlib.reload(config_module)

    assert config_module.config_data.redis_url == "redis://127.0.0.1:6379"
