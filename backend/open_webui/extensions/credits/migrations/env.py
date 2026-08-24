from __future__ import annotations

from open_webui.extensions.credits.migrations.runner import SPEC
from open_webui.extensions.credits.models import (  # noqa: F401 — 副作用导入，注册全部表
    CreditAccount,
    CreditLedger,
    CreditPrice,
    CreditUsage,
)
from open_webui.extensions.migration_kit.env import run_env

run_env(SPEC)
