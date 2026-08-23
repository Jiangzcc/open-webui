from __future__ import annotations

from open_webui.extensions.migration_kit.env import run_env
from open_webui.extensions.model_ops.migrations.runner import SPEC
from open_webui.extensions.model_ops.models import ImageModelOperation  # noqa: F401 — 副作用导入，注册全部表

run_env(SPEC)
