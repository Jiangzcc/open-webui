import sys
from pathlib import Path
from types import ModuleType

from open_webui import windows_server


def test_windows_script_uses_application_cli_for_selector_event_loop() -> None:
    script = (Path(__file__).parents[3] / 'start_windows.bat').read_text(encoding='utf-8')

    assert 'python -m open_webui.windows_server' in script
    assert 'uvicorn open_webui.main:app' not in script


def test_windows_runner_disables_uvicorn_loop_override(monkeypatch) -> None:
    main_module = ModuleType('open_webui.main')
    env_module = ModuleType('open_webui.env')
    env_module.UVICORN_WORKERS = 1
    captured: dict[str, object] = {}

    monkeypatch.setenv('HOST', '127.0.0.1')
    monkeypatch.setenv('PORT', '8765')
    monkeypatch.setenv('FORWARDED_ALLOW_IPS', "'*'")
    monkeypatch.setitem(sys.modules, 'open_webui.main', main_module)
    monkeypatch.setitem(sys.modules, 'open_webui.env', env_module)
    monkeypatch.setattr(windows_server.uvicorn, 'run', lambda *args, **kwargs: captured.update(kwargs))

    windows_server.main()

    assert captured == {
        'host': '127.0.0.1',
        'port': 8765,
        'forwarded_allow_ips': '*',
        'workers': 1,
        'loop': 'none',
        'ws': 'auto',
    }
