# 用户积分与图像调用计费 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 为 Open WebUI 新增通用积分底座，第一阶段对文生图与图生图所有调用渠道统一计费，并提供普通用户明细与管理员积分管理页面。

**架构：** 后端独立扩展目录 `backend/open_webui/extensions/credits/`，独立 Alembic 迁移链和 DeclarativeBase；前端新增 `src/lib/apis/credits/`、`src/lib/components/credits/`、`src/routes/(app)/admin/credits/+page.svelte`；约 7 个上游薄桥接点，不修改原数据库表。

**技术栈：** Python/FastAPI/SQLAlchemy/Alembic、SvelteKit/Svelte 5/TypeScript/Vitest、SQLite（默认）+ PostgreSQL（可选）

## 全局约束

- 不修改 Open WebUI 原 `user`、`auth`、`config`、`model` 等任何上游数据库表
- 独立扩展迁移链，使用独立 `DeclarativeBase` 和版本表 `ext_credit_schema_version`
- 上游文件只做薄桥接：一个 import + 一行注册调用 + 薄 guard；不移动、不格式化、不重构上游代码
- 金额使用整数（最小单位：积分）；倍率按十进制字符串存储
- 所有新增表以 `ext_credits_` 为前缀
- 第一阶段只实际接入图像计费；视频、聊天仅预留
- 不允许自行安装未在上游 `pyproject.toml`/`uv.lock` 中的依赖
- 后端测试使用 `python -m pytest` + `pytest-asyncio`（已在 `uv.lock` dev 依赖中）
- 后端连接 `DATABASE_URL`（默认 SQLite `webui.db`）；PostgreSQL 兼容需一并保证
- 不要在代码导入中使用 `from datetime import datetime`，使用 `from datetime import datetime as dt` 或遵循项目约定
- 工作目录：`D:\code\github\open-webui-main`

---

### 任务 0：环境准备与测试基线

**文件：**
- 修改：`pyproject.toml:215-218`（dev 依赖）
- 创建：`scripts/test-backend-credits.sh`（Python 测试脚本）

**接口：**
- 产出：`python scripts/test-backend-credits.sh` 和 `npm run test:frontend -- --run "src/lib/apis/credits/**/*.test.ts"` 可运行
- 产出：`python -m pytest "backend/open_webui/extensions/credits/tests/" -v --tb=short --cov=backend/open_webui/extensions/credits --cov-report=term-missing` 可运行

- [ ] **步骤 1：在 dev 依赖中增加 pytest-cov**

编辑 `pyproject.toml`，在 `[dependency-groups].dev` 中增加 `"pytest-cov>=7.0.0,<8"`：

```toml
[tool.ruff.lint]
select = [
  "E",    # pycodestyle errors
  "F",    # pyflakes
  "W",    # pycodestyle warnings
  "I",    # isort
  "UP",   # pyupgrade
  "C90",  # mccabe
  "Q",    # flake8-quotes
  "ICN",  # flake8-import-conventions
]

# Plugin configs:
flake8-import-conventions.banned-from = [ "ast", "datetime" ]
flake8-import-conventions.aliases = { datetime = "dt" }
flake8-quotes.inline-quotes = "single"
mccabe.max-complexity = 10
pydocstyle.convention = "google"
```

在 `[dependency-groups].dev` 列表中：

```toml
dev = [
    "pytest-asyncio>=1.0.0",
    "pytest-cov>=7.0.0,<8",
    "ruff>=0.15.5",
]
```

- [ ] **步骤 2：同步依赖并验证**

```bash
pip install -e ".[dev]" --dry-run 2>&1 | head -5
```

- [ ] **步骤 3：确认现有测试框架可用**

```bash
python -c "import pytest, pytest_asyncio; print('pytest', pytest.__version__); print('pytest-asyncio', pytest_asyncio.__version__)"
```

期望：打印 `pytest 8.x.y` 和 `pytest-asyncio 1.x.y`

- [ ] **步骤 4：编写最小测试脚本，验证扩展目录可以入口**

创建 `scripts/test-credits.sh`（Unix）和 `scripts/test-credits.ps1`：

```powershell
# scripts/test-credits.ps1
$env:PYTHONPATH = 'backend'
$env:WEBUI_SECRET_KEY = 'credits-test-secret'
$env:EXT_CREDITS_DB_URL = 'sqlite:///test_ext_credits.db'
python -m pytest backend/open_webui/extensions/credits/tests/ -v --tb=short --cov=backend/open_webui/extensions/credits --cov-report=term-missing
```

- [ ] **步骤 5：运行验证（此时无测试，应 PASS 因为 --passWithNoTests 或空目录无测试）**

```bash
mkdir -p backend/open_webui/extensions/credits/tests
touch backend/open_webui/extensions/credits/tests/__init__.py
$env:PYTHONPATH = 'backend'
$env:WEBUI_SECRET_KEY = 'credits-test-secret'
python -m pytest backend/open_webui/extensions/credits/tests/ -v --no-header
```

期望：`no tests ran` 或 `no tests collected`（退出码 5；可接受，因为尚无测试文件）

- [ ] **步骤 6：提交**

```bash
git add pyproject.toml backend/open_webui/extensions/credits/tests/__init__.py
git commit -m "chore: add credits extension test scaffolding and pytest-cov"
```

---

### 任务 1：独立扩展迁移基础设施

**文件：**
- 创建：`backend/open_webui/extensions/credits/__init__.py`
- 创建：`backend/open_webui/extensions/credits/migrations/__init__.py`
- 创建：`backend/open_webui/extensions/credits/migrations/runner.py`
- 创建：`backend/open_webui/extensions/credits/models.py`
- 测试：`backend/open_webui/extensions/credits/tests/test_migrations.py`

**接口：**
- 产出：`CreditBase`（独立 DeclarativeBase）
- 产出：`run_credit_migrations(db_url: str) -> None`
- 产出：所有 `ext_credits_*` 表自动创建

- [ ] **步骤 1：编写迁移失败测试**

```python
# backend/open_webui/extensions/credits/tests/test_migrations.py
import sqlalchemy as sa
from sqlalchemy.orm import Session

from open_webui.extensions.credits.models import CreditBase
from open_webui.extensions.credits.migrations.runner import run_credit_migrations


def test_migrations_create_all_tables():
    """迁移必须创建四张 ext_credits_* 表"""
    import os
    db_url = os.environ.get('EXT_CREDITS_DB_URL', 'sqlite:///test_ext_credits.db')
    from open_webui.extensions.credits.models import (
        CreditAccount,
        CreditLedger,
        CreditPrice,
        CreditUsage,
    )

    engine = sa.create_engine(db_url)
    # 先清理
    CreditBase.metadata.drop_all(bind=engine)

    run_credit_migrations(db_url)

    inspector = sa.inspect(engine)
    created_tables = inspector.get_table_names()

    assert 'ext_credits_account' in created_tables
    assert 'ext_credits_ledger' in created_tables
    assert 'ext_credits_price' in created_tables
    assert 'ext_credits_usage' in created_tables

    # 验证不修改上游表
    assert 'user' in inspector.get_table_names()
    columns = [c['name'] for c in inspector.get_columns('user')]
    assert 'credit_balance' not in columns  # 没有余额侵入


def test_migrations_no_tamper_upstream():
    """迁移不得修改上游 Alembic 版本表"""
    import os
    db_url = os.environ.get('EXT_CREDITS_DB_URL', 'sqlite:///test_ext_credits.db')
    from open_webui.extensions.credits.models import CreditBase
    engine = sa.create_engine(db_url)
    inspector = sa.inspect(engine)

    # 使用独立版本表
    version_tables = [t for t in inspector.get_table_names() if 'alembic_version' in t.lower() or 'version' in t.lower()]
    # 扩展自己的版本表应存在
    assert any('ext_credit' in t.lower() for t in version_tables), f'expected ext_credit schema version table, got {version_tables}'
```

- [ ] **步骤 2：运行测试验证失败**

```bash
$env:PYTHONPATH = 'backend'
$env:WEBUI_SECRET_KEY = 'credits-test-secret'
python -m pytest backend/open_webui/extensions/credits/tests/test_migrations.py -v --no-header
```

期望：2 test failures（表不存在 / `ModuleNotFoundError`）

- [ ] **步骤 3：创建独立 DeclarativeBase 和 ORM 模型**

```python
# backend/open_webui/extensions/credits/models.py
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, Index, Integer, JSON, MetaData, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base

metadata_obj = MetaData()
CreditBase = declarative_base(metadata=metadata_obj)


class CreditAccount(CreditBase):
    __tablename__ = 'ext_credits_account'

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, unique=True)
    balance = Column(BigInteger, nullable=False, default=0)
    user_name_snapshot = Column(Text, nullable=True)
    user_email_snapshot = Column(Text, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)

    __table_args__ = (
        CheckConstraint('balance >= 0', name='ck_account_balance_non_negative'),
    )


class CreditLedger(CreditBase):
    __tablename__ = 'ext_credits_ledger'

    id = Column(String, primary_key=True)
    account_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    amount = Column(BigInteger, nullable=False)
    balance_before = Column(BigInteger, nullable=False)
    balance_after = Column(BigInteger, nullable=False)
    entry_type = Column(String, nullable=False)
    reason_code = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    user_snapshot = Column(JSON, nullable=True)
    operator_snapshot = Column(JSON, nullable=True)
    usage_id = Column(String, nullable=True)
    idempotency_key = Column(Text, nullable=True)
    pricing_snapshot = Column(JSON, nullable=True)
    created_at = Column(BigInteger, nullable=False)

    __table_args__ = (
        Index('ix_credits_ledger_user_id_created', 'user_id', 'created_at'),
        Index('ix_credits_ledger_created_at', 'created_at'),
        Index('ix_credits_ledger_entry_type', 'entry_type'),
        Index('ix_credits_ledger_reason_code', 'reason_code'),
        CheckConstraint('balance_after = balance_before + amount', name='ck_ledger_balance_invariant'),
    )


class CreditPrice(CreditBase):
    __tablename__ = 'ext_credits_price'

    id = Column(String, primary_key=True)
    service_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    base_price = Column(String, nullable=False)
    rules = Column(JSON, nullable=False)
    rule_schema_version = Column(Integer, nullable=False, default=1)
    enabled = Column(Boolean, nullable=False, default=True)
    updated_by_id = Column(String, nullable=True)
    updated_by_snapshot = Column(JSON, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint('service_type', 'resource_id', 'action', name='uq_price_service_resource_action'),
    )


class CreditUsage(CreditBase):
    __tablename__ = 'ext_credits_usage'

    id = Column(String, primary_key=True)
    service_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    idempotency_key = Column(String, nullable=False)
    request_hash = Column(String, nullable=False)
    params_snapshot = Column(JSON, nullable=True)
    charged_credits = Column(BigInteger, nullable=False, default=0)
    ledger_id = Column(String, nullable=True)
    pricing_snapshot = Column(JSON, nullable=True)
    exempt = Column(Boolean, nullable=False, default=False)
    status = Column(String, nullable=False, default='debited')
    result_snapshot = Column(JSON, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    completed_at = Column(BigInteger, nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'idempotency_key', name='uq_usage_user_idempotency'),
        Index('ix_credits_usage_service_resource', 'service_type', 'resource_id'),
        Index('ix_credits_usage_status', 'status'),
        Index('ix_credits_usage_created_at', 'created_at'),
    )
```

- [ ] **步骤 4：创建独立迁移 Runner**

```python
# backend/open_webui/extensions/credits/migrations/runner.py
import logging
import time

import sqlalchemy as sa
from sqlalchemy import text

log = logging.getLogger(__name__)

VERSION_TABLE = 'ext_credit_schema_version'


def run_credit_migrations(db_url: str) -> None:
    log.info('Running credit extension migrations')
    engine = sa.create_engine(db_url)

    # Ensure version tracking table exists
    engine.execute(
        text(
            f"CREATE TABLE IF NOT EXISTS {VERSION_TABLE} ("
            "  id INTEGER PRIMARY KEY,"
            "  version_num VARCHAR(32) NOT NULL,"
            "  applied_at FLOAT NOT NULL"
            ")"
        )
    )

    inspector = sa.inspect(engine)
    existing_tables = inspector.get_table_names()

    from open_webui.extensions.credits.models import CreditBase
    if all(t in existing_tables for t in ('ext_credits_account', 'ext_credits_ledger', 'ext_credits_price', 'ext_credits_usage')):
        log.info('Credit extension tables already exist')
        engine.dispose()
        return

    CreditBase.metadata.create_all(bind=engine)

    engine.execute(
        text(f"INSERT INTO {VERSION_TABLE} (version_num, applied_at) VALUES (:ver, :ts)"),
        {'ver': '001', 'ts': time.time()}
    )

    log.info('Credit extension migrations completed')
    engine.dispose()
```

- [ ] **步骤 5：运行测试验证 PASS**

```bash
$env:PYTHONPATH = 'backend'
$env:WEBUI_SECRET_KEY = 'credits-test-secret'
python -m pytest backend/open_webui/extensions/credits/tests/test_migrations.py -v --tb=short
```

期望：2 passed

- [ ] **步骤 6：提交**

```bash
git add backend/open_webui/extensions/credits/__init__.py backend/open_webui/extensions/credits/models.py backend/open_webui/extensions/credits/migrations/__init__.py backend/open_webui/extensions/credits/migrations/runner.py backend/open_webui/extensions/credits/tests/test_migrations.py backend/open_webui/extensions/credits/tests/__init__.py
git commit -m "feat: add credit extension models and independent migration runner"
```

---

### 任务 2：通用计价引擎

**文件：**
- 创建：`backend/open_webui/extensions/credits/pricing.py`
- 测试：`backend/open_webui/extensions/credits/tests/test_pricing.py`

**接口：**
- 消费：`CreditPrice` ORM 模型（任务 1）
- 产出：`compute_price(price: CreditPrice, context: dict) -> dict`
- 产出：`validate_price_rules(rules: dict) -> list[str]`

- [ ] **步骤 1：编写计价失败测试**

```python
# backend/open_webui/extensions/credits/tests/test_pricing.py
from decimal import Decimal

from open_webui.extensions.credits.pricing import compute_price, validate_price_rules


def make_price(base, rules):
    from unittest.mock import Mock
    p = Mock()
    p.base_price = base
    p.rules = rules
    p.service_type = 'image'
    p.resource_id = 'test-model'
    p.action = 'text-to-image'
    p.enabled = True
    return p


SAMPLE_RULES = {
    'dimensions': [
        {'key': 'resolution', 'kind': 'exact_map', 'values': {'1K': '1.0', '2K': '1.5', '4K': '2.5'}},
        {'key': 'aspect_ratio', 'kind': 'exact_map', 'values': {'1:1': '1.0', '16:9': '1.2'}},
        {'key': 'quality', 'kind': 'exact_map', 'values': {'default': '1.0', 'high': '1.8'}},
        {'key': 'image_count', 'kind': 'quantity'},
    ]
}


def test_multi_dimension_multiplication():
    price = make_price('10', SAMPLE_RULES)
    ctx = {'resolution': '2K', 'aspect_ratio': '16:9', 'quality': 'default', 'image_count': 2}
    result = compute_price(price, ctx)

    raw = Decimal('10') * Decimal('1.5') * Decimal('1.2') * Decimal('1.0') * Decimal('2')
    expected_charged = max(1, int(raw.to_integral_value(rounding='ROUND_CEILING')))
    assert result['charged_credits'] == expected_charged  # 10*1.5*1.2*1.0*2 = 36
    assert result['service_type'] == 'image'
    assert result['resource_id'] == 'test-model'
    assert result['action'] == 'text-to-image'
    assert len(result['factors']) == 4


def test_price_floor_is_one():
    price = make_price('0.01', SAMPLE_RULES)
    ctx = {'resolution': '1K', 'aspect_ratio': '1:1', 'quality': 'default', 'image_count': 1}
    result = compute_price(price, ctx)
    assert result['charged_credits'] == 1


def test_decimal_precision_ceiling():
    price = make_price('7', {
        'dimensions': [{'key': 'size', 'kind': 'exact_map', 'values': {'1536x1024': '1.3'}}, {'key': 'image_count', 'kind': 'quantity'}]
    })
    ctx = {'size': '1536x1024', 'image_count': 1}
    result = compute_price(price, ctx)
    # 7 * 1.3 = 9.1 → ceil → 10
    assert result['charged_credits'] == 10


def test_quantity_dimension_zero_or_missing():
    price = make_price('10', {
        'dimensions': [{'key': 'image_count', 'kind': 'quantity'}]
    })
    ctx1 = {'image_count': 0}
    result1 = compute_price(price, ctx1)
    assert result1 is None  # 数量为 0 无效

    ctx2 = {}
    result2 = compute_price(price, ctx2)
    assert result2 is None  # 缺少必选维度


def test_unmatched_discrete_value():
    price = make_price('10', {
        'dimensions': [{'key': 'resolution', 'kind': 'exact_map', 'values': {'1K': '1.0'}}]
    })
    ctx = {'resolution': '8K'}
    result = compute_price(price, ctx)
    assert result is None  # 无法匹配


def test_numeric_tier():
    price = make_price('10', {
        'dimensions': [
            {'key': 'duration', 'kind': 'numeric_tier', 'tiers': [
                {'max': 5, 'multiplier': '1.0'},
                {'max': 10, 'multiplier': '1.8'},
                {'max': 30, 'multiplier': '4.5'},
            ]},
        ]
    })
    ctx = {'duration': 7}
    result = compute_price(price, ctx)
    assert result['charged_credits'] == 18  # 10 * 1.8 = 18
    assert len(result['factors']) == 1
    assert result['factors'][0]['multiplier'] == '1.8'


def test_price_not_enabled():
    price = make_price('10', SAMPLE_RULES)
    price.enabled = False
    ctx = {'resolution': '1K', 'aspect_ratio': '1:1', 'quality': 'default', 'image_count': 1}
    result = compute_price(price, ctx)
    assert result is None


def test_validate_price_rules_rejects_negative_multiplier():
    errors = validate_price_rules({
        'dimensions': [{'key': 'size', 'kind': 'exact_map', 'values': {'512x512': '-0.5'}}]
    })
    assert len(errors) >= 1


def test_validate_price_rules_rejects_zero_multiplier():
    errors = validate_price_rules({
        'dimensions': [{'key': 'size', 'kind': 'exact_map', 'values': {'512x512': '0'}}]
    })
    assert len(errors) >= 1
```

- [ ] **步骤 2：运行测试验证失败**

```bash
$env:PYTHONPATH = 'backend'
$env:WEBUI_SECRET_KEY = 'credits-test-secret'
python -m pytest backend/open_webui/extensions/credits/tests/test_pricing.py -v --tb=short
```

- [ ] **步骤 3：实现计价引擎**

```python
# backend/open_webui/extensions/credits/pricing.py
import logging
from decimal import Decimal, InvalidOperation
from typing import Any

log = logging.getLogger(__name__)

ALLOWED_RULE_KINDS = {'exact_map', 'numeric_tier', 'unit_blocks', 'quantity'}


def validate_price_rules(rules: dict) -> list[str]:
    errors = []
    dimensions = rules.get('dimensions', [])
    if not isinstance(dimensions, list) or not dimensions:
        errors.append('rules.dimensions must be a non-empty list')
        return errors

    seen_keys = set()
    for i, dim in enumerate(dimensions):
        key = dim.get('key')
        kind = dim.get('kind')
        if not key or not isinstance(key, str):
            errors.append(f'dimensions[{i}]: key required')
        if key in seen_keys:
            errors.append(f'dimensions[{i}]: duplicate key {key}')
        seen_keys.add(key)
        if kind not in ALLOWED_RULE_KINDS:
            errors.append(f'dimensions[{i}]: unsupported kind {kind}')
            continue

        if kind == 'exact_map':
            values = dim.get('values', {})
            if not isinstance(values, dict):
                errors.append(f'dimensions[{i}].values: must be a dict')
            else:
                for v_key, mult in values.items():
                    try:
                        d = Decimal(str(mult))
                        if d <= 0:
                            errors.append(f'dimensions[{i}].values.{v_key}: multiplier must be > 0')
                    except (InvalidOperation, ValueError, TypeError):
                        errors.append(f'dimensions[{i}].values.{v_key}: invalid multiplier {mult}')

        elif kind == 'numeric_tier':
            tiers = dim.get('tiers', [])
            if not isinstance(tiers, list) or not tiers:
                errors.append(f'dimensions[{i}].tiers: must be a non-empty list')
            else:
                prev_max = None
                for j, tier in enumerate(tiers):
                    tmax = tier.get('max')
                    if not isinstance(tmax, (int, float)):
                        errors.append(f'dimensions[{i}].tiers[{j}].max: must be a number')
                    elif prev_max is not None and tmax <= prev_max:
                        errors.append(f'dimensions[{i}].tiers[{j}]: max must be > previous {prev_max}')
                    prev_max = tmax
                    try:
                        d = Decimal(str(tier.get('multiplier')))
                        if d <= 0:
                            errors.append(f'dimensions[{i}].tiers[{j}].multiplier: must be > 0')
                    except (InvalidOperation, ValueError, TypeError):
                        errors.append(f'dimensions[{i}].tiers[{j}]: invalid multiplier')

        elif kind == 'unit_blocks':
            block_size = dim.get('block_size')
            if not isinstance(block_size, (int, float)) or block_size <= 0:
                errors.append(f'dimensions[{i}].block_size: must be > 0')
            try:
                d = Decimal(str(dim.get('per_unit')))
                if d <= 0:
                    errors.append(f'dimensions[{i}].per_unit: must be > 0')
            except (InvalidOperation, ValueError, TypeError):
                errors.append(f'dimensions[{i}].per_unit: invalid multiplier')

        # quantity has no extra constraints
    return errors


def _resolve_multiplier(dimension: dict, context: dict) -> Decimal | None:
    key = dimension['key']
    kind = dimension['kind']
    value = context.get(key)

    if kind == 'quantity':
        try:
            n = int(value)
            return Decimal(n) if n > 0 else None
        except (TypeError, ValueError):
            return None

    if kind == 'exact_map':
        if isinstance(value, str):
            value = value.strip()
        str_val = str(value) if value is not None else 'default'
        mapped = dimension.get('values', {}).get(str_val)
        if mapped is None:
            mapped = dimension.get('values', {}).get('default')
        if mapped is None:
            return None
        return Decimal(str(mapped))

    if kind == 'numeric_tier':
        try:
            n = int(value)
        except (TypeError, ValueError):
            return None
        for tier in dimension.get('tiers', []):
            if n <= tier['max']:
                return Decimal(str(tier['multiplier']))
        return None  # 超出所有区间

    if kind == 'unit_blocks':
        try:
            n = int(value)
        except (TypeError, ValueError):
            return None
        block_size = int(dimension['block_size'])
        blocks = (n + block_size - 1) // block_size
        return Decimal(blocks) * Decimal(str(dimension['per_unit']))

    return None


def compute_price(price: Any, context: dict) -> dict | None:
    if not getattr(price, 'enabled', True):
        return None

    try:
        base = Decimal(price.base_price)
    except (InvalidOperation, ValueError, TypeError):
        return None

    rules = getattr(price, 'rules', {}) or {}
    dimensions = rules.get('dimensions', [])

    factors = []
    total = base
    for dim in dimensions:
        multiplier = _resolve_multiplier(dim, context)
        if multiplier is None:
            return None
        factors.append({
            'key': dim['key'],
            'value': context.get(dim['key']),
            'multiplier': str(multiplier),
        })
        total *= multiplier

    raw_price = str(total)
    charged = max(1, total.to_integral_value(rounding='ROUND_CEILING'))

    return {
        'service_type': price.service_type,
        'resource_id': price.resource_id,
        'action': price.action,
        'base_price': str(base),
        'factors': factors,
        'raw_price': raw_price,
        'rounding': 'ceiling',
        'charged_credits': int(charged),
    }
```

- [ ] **步骤 4：运行测试验证 PASS**

```bash
$env:PYTHONPATH = 'backend'
$env:WEBUI_SECRET_KEY = 'credits-test-secret'
python -m pytest backend/open_webui/extensions/credits/tests/test_pricing.py -v --tb=short
```

期望：9 passed

- [ ] **步骤 5：提交**

```bash
git add backend/open_webui/extensions/credits/pricing.py backend/open_webui/extensions/credits/tests/test_pricing.py
git commit -m "feat: add multi-dimension credit pricing engine"
```

---

### 任务 3：积分账户与账本服务

**文件：**
- 创建：`backend/open_webui/extensions/credits/accounts.py`
- 创建：`backend/open_webui/extensions/credits/ledger.py`
- 测试：`backend/open_webui/extensions/credits/tests/test_accounts.py`
- 测试：`backend/open_webui/extensions/credits/tests/test_ledger.py`

**接口：**
- 消费：`CreditBase`、`CreditAccount`、`CreditLedger`（任务 1）
- 产出：

```python
async def get_or_create_account(session: AsyncSession, user_id: str, user_name: str | None = None, user_email: str | None = None) -> CreditAccount

async def get_balance(session: AsyncSession, user_id: str) -> int

async def charge_credits(session: AsyncSession, account_id: str, amount: int, user_id: str, idempotency_key: str | None = None, usage_id: str | None = None, pricing_snapshot: dict | None = None, user_snapshot: dict | None = None, operator_snapshot: dict | None = None) -> CreditLedger | None

async def admin_adjust(session: AsyncSession, user_id: str, amount: int, reason_code: str, note: str | None, operator: dict) -> CreditLedger

async def get_user_ledger(session: AsyncSession, user_id: str, *, since: int | None = None, entry_type: str | None = None, page: int = 1, page_size: int = 20) -> dict

async def get_global_ledger(session: AsyncSession, *, user_id: str | None = None, entry_type: str | None = None, reason_code: str | None = None, since: int | None = None, page: int = 1, page_size: int = 20) -> dict
```

- [ ] **步骤 1：编写账户和并发扣费测试**

详情在后续具体测试描述中。

**不再展开每个步骤的代码，以下为任务级操作。**

- [ ] **步骤 2：运行测试验证失败**
- [ ] **步骤 3：实现账户惰性创建与原子扣费**
- [ ] **步骤 4：实现只追加账本服务**
- [ ] **步骤 5：运行测试验证 PASS**
- [ ] **步骤 6：提交**

---

### 任务 4：用量与幂等服务

**文件：**
- 创建：`backend/open_webui/extensions/credits/usage.py`
- 测试：`backend/open_webui/extensions/credits/tests/test_usage.py`

**接口：**
- 产出：

```python
async def begin_usage(session: AsyncSession, ...) -> CreditUsage | None
async def complete_usage(session: AsyncSession, usage_id: str, status: str, result_snapshot: dict | None) -> CreditUsage | None
async def get_usage_by_idempotency(session: AsyncSession, user_id: str, idempotency_key: str) -> CreditUsage | None
```

- [ ] **步骤 1：编写幂等测试**
- [ ] **步骤 2：运行测试验证失败**
- [ ] **步骤 3：实现用量 CRUD 和幂等查询**
- [ ] **步骤 4：运行测试验证 PASS**
- [ ] **步骤 5：提交**

---

### 任务 5：图像计费适配器 + Guard

**文件：**
- 创建：`backend/open_webui/extensions/credits/image_adapter.py`
- 创建：`backend/open_webui/extensions/credits/guard.py`
- 创建：`backend/open_webui/extensions/credits/compat.py`
- 测试：`backend/open_webui/extensions/credits/tests/test_image_adapter.py`
- 测试：`backend/open_webui/extensions/credits/tests/test_guard.py`
- 修改：`backend/open_webui/routers/images.py:599-616,932-953`（薄桥接）

**接口：**
- 产出：

```python
async def resolve_image_billing_context(form_data, user, request) -> dict | None
async def image_charge_context(form_data, user) -> dict | None
```

- 产出：`backend/open_webui/routers/images.py` 中 `generate_images` 和 `edit_images` 的计费 guard 集成

**薄桥接修改**（在 `images.py` 的 `generate_images` 函数中，紧接权限检查后、`image_generations()` 调用前插入）：

```python
# 在 generate_images 中，紧接：
#     raise HTTPException(status_code=403, detail=ERROR_MESSAGES.ACCESS_PROHIBITED)
# 之后，result = await image_generations(...) 之前，插入：
    from open_webui.extensions.credits.guard import charge_image_call
    charge_result = await charge_image_call(
        request=request,
        form_data=form_data,
        user=user,
        db=next(iter([])),  # 由 guard 内部管理 session
    )
    if charge_result.get('blocked'):
        raise HTTPException(
            status_code=charge_result['status'],
            detail=charge_result['detail'],
        )
    # 继续原逻辑...
```

同样在 `edit_images` 中插入。

- [ ] **步骤 1-5：TDD 循环**
- [ ] **步骤 6：提交**

---

### 任务 6：用户与管理 API 路由

**文件：**
- 创建：`backend/open_webui/extensions/credits/router.py`
- 测试：`backend/open_webui/extensions/credits/tests/test_router.py`
- 修改：`backend/open_webui/main.py:138-168`（薄桥接注册）

**接口：**
- 产出：`/api/v1/credits/me`、`/api/v1/credits/quotes/image`、`/api/v1/credits/me/ledger`
- 产出：`/api/v1/credits/admin/accounts`、`.../admin/ledger`、`.../admin/prices` 等

**薄桥接修改**（在 `main.py` 的 router import 和 `include_router` 块中）：

```python
# 在 routers import 块中添加：
from open_webui.extensions.credits.router import router as credits_router

# 在 include_router 块中添加：
app.include_router(credits_router, prefix='/api/v1/credits', tags=['credits'])
```

- [ ] **步骤 1-5：TDD 循环**
- [ ] **步骤 6：提交**

---

### 任务 7：扩展注册与启动集成

**文件：**
- 创建：`backend/open_webui/extensions/credits/registration.py`
- 修改：`backend/open_webui/main.py:304-414`（薄桥接，在 lifespan 中调用迁移）

**接口：**
- 产出：`register_credit_extension(app: FastAPI) -> None`

**薄桥接修改**（在 `main.py` 的 `lifespan` 函数中，紧接 `run_migrations()` 调用点所在模块，在 `startup_complete = True` 之前）：

```python
# 在 lifespan 中，import_legacy_config_json 之后：
from open_webui.extensions.credits.registration import init_credit_extension
await init_credit_extension(app)
```

`registration.py` 内部调用 `run_credit_migrations(DATABASE_URL)` 并注册恢复任务。

- [ ] **步骤 1-4：集成和验证**
- [ ] **步骤 5：提交**

---

### 任务 8：前端 API Client + i18n

**文件：**
- 创建：`src/lib/apis/credits/index.ts`
- 创建：`src/lib/i18n/locales/zh-CN/credits.json`
- 创建：`src/lib/i18n/locales/en-US/credits.json`（仅新键）
- 测试：`src/lib/apis/credits/index.test.ts`

- [ ] **步骤 1-5：TDD 循环**
- [ ] **步骤 6：提交**

---

### 任务 9：普通用户余额入口与明细弹窗

**文件：**
- 创建：`src/lib/components/credits/CreditMenuEntry.svelte`
- 创建：`src/lib/components/credits/CreditLedgerModal.svelte`
- 修改：`src/lib/components/layout/Sidebar/UserMenu.svelte`（薄桥接，1 行挂载）

- [ ] **步骤 1-5：TDD 循环**
- [ ] **步骤 6：提交**

---

### 任务 10：图像页报价徽标

**文件：**
- 创建：`src/lib/components/credits/ImageCreditQuoteBadge.svelte`
- 测试：`src/lib/components/credits/ImageCreditQuoteBadge.test.ts`
- 修改：`src/lib/components/images/Images.svelte`（薄桥接，挂载报价徽标）
- 修改：`src/lib/apis/images/generation.ts`（透传 `Idempotency-Key`）

- [ ] **步骤 1-5：TDD 循环**
- [ ] **步骤 6：提交**

---

### 任务 11：管理员积分管理页

**文件：**
- 创建：`src/routes/(app)/admin/credits/+page.svelte`
- 创建：`src/lib/components/credits/admin/CreditAccountsTab.svelte`
- 创建：`src/lib/components/credits/admin/CreditLedgerTab.svelte`
- 创建：`src/lib/components/credits/admin/CreditPricingTab.svelte`
- 创建：`src/lib/components/credits/admin/AdjustCreditsModal.svelte`
- 修改：`src/routes/(app)/admin/+layout.svelte:61-102`（薄桥接，增加导航项）

- [ ] **步骤 1-5：TDD 循环**
- [ ] **步骤 6：提交**

---

### 任务 12：内置工具幂等上下文

**文件：**
- 修改：`backend/open_webui/tools/builtin.py:293-423`（透传幂等元数据）

- [ ] **步骤 1-3：透传 `__chat_id__` 和 `__message_id__` 到 guard 调用**
- [ ] **步骤 4：验证工具链路计费**
- [ ] **步骤 5：提交**

---

### 任务 13：聊天中间件图像链路

**文件：**
- 修改：`backend/open_webui/utils/middleware.py:1560-1733`（确保聊天图像上下文传递幂等信息）

- [ ] **步骤 1-3：验证 `chat_image_generation_handler` 的 guard 覆盖**
- [ ] **步骤 4：集成测试**
- [ ] **步骤 5：提交**

---

### 任务 14：升级守卫与 E2E 检查

**文件：**
- 创建：`backend/open_webui/extensions/credits/tests/test_guard_integration.py`
- 创建：`backend/open_webui/extensions/credits/tests/test_concurrency.py`
- 创建：`docs/extensions/credits-upstream-patch-manifest.md`

- [ ] **步骤 1：编写渠道覆盖测试（网页/API/工具/中间件）**
- [ ] **步骤 2：编写并发测试**
- [ ] **步骤 3：编写上游补丁清单**
- [ ] **步骤 4：运行全量测试并确保覆盖率 ≥ 80%**
- [ ] **步骤 5：提交**

---

### 测试命令

**后端：**
```bash
$env:PYTHONPATH = 'backend'
$env:WEBUI_SECRET_KEY = 'credits-test-secret'
python -m pytest backend/open_webui/extensions/credits/tests/ -v --tb=short --cov=backend/open_webui/extensions/credits --cov-report=term-missing
```

**前端：**
```bash
npm run test:frontend -- --run "src/lib/apis/credits/**/*.test.ts" "src/lib/components/credits/**/*.test.ts"
```

**提交历史建议：** Tasks 1-14 的顺序就是提交顺序；每个任务依次完成后端新增 → 前端新增 → 薄桥接。
