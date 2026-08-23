from __future__ import annotations

from open_webui.extensions.migration_kit.env import run_env
from open_webui.extensions.provider_ops.migrations.runner import SPEC
from open_webui.extensions.provider_ops.models import (  # noqa: F401 — 副作用导入，注册全部表
    ProviderAnalyticsBucket,
    ProviderBillingEvent,
    ProviderInvocation,
    ProviderPriceSnapshot,
    ProviderSyncRun,
    ProviderUsageBucket,
)

run_env(SPEC)
