"""Source-level entry-point contract tests for Task 6.

These tests deliberately parse ``routers/images.py`` with ``ast`` instead of
importing it. Importing the module pulls in the upstream Alembic migration
chain, which is environmentally unreliable on this machine (see the
``credits-test-import-block`` memory). The bridging contracts they pin are
structural: which values the provider branches return, how the edit invoke
closure orders reference snapshots, and which authorization scope each call
site supplies. Dynamic behaviour is exercised by the creations capture/service
suites and by Task 11's real-browser acceptance.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_IMAGES_PATH = Path(__file__).resolve().parents[3] / 'routers' / 'images.py'
_MIDDLEWARE_PATH = Path(__file__).resolve().parents[3] / 'utils' / 'middleware.py'
_BUILTIN_PATH = Path(__file__).resolve().parents[3] / 'tools' / 'builtin.py'
_GENERATION_TASKS_PATH = Path(__file__).resolve().parents[1] / 'generation_tasks.py'
_FAL_BRIDGE_PATH = Path(__file__).resolve().parents[2] / 'images' / 'fal_bridge.py'

_GATE_CALLS = (
    'enforce_image_generation_rate(',
    'acquire_image_generation_slot(',
    'release_image_generation_slot(',
)


def _load(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding='utf-8'))


def _func_defs(module: ast.Module) -> dict[str, ast.AsyncFunctionDef | ast.FunctionDef]:
    defs: dict[str, ast.AsyncFunctionDef | ast.FunctionDef] = {}
    for node in ast.walk(module):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            defs[node.name] = node
    return defs


def _contains(node: ast.AST, predicate) -> bool:
    return any(predicate(child) for child in ast.walk(node))


def _returns_constructor_named(node: ast.AST, name: str) -> bool:
    def pred(child: ast.AST) -> bool:
        return (
            isinstance(child, ast.Return)
            and isinstance(child.value, ast.Call)
            and isinstance(child.value.func, ast.Name)
            and child.value.func.id == name
        )

    return _contains(node, pred)


@pytest.fixture(scope='module')
def images_tree():
    return _load(_IMAGES_PATH)


@pytest.fixture(scope='module')
def images_funcs(images_tree):
    return _func_defs(images_tree)


def test_image_generations_and_edits_require_authorization_scope(images_funcs) -> None:
    # metadata/user：二开新增 —— 由 creations 调度链传入（任务捕获等）。
    # 门禁包装器与 core 函数共享同一位置签名（复盘 P0-3 下沉后 core 承载原函数体）。
    for name in (
        'image_generations',
        'image_edits',
        '_image_generations_core',
        '_image_edits_core',
    ):
        params = [a.arg for a in images_funcs[name].args.args]
        assert params == [
            'request',
            'form_data',
            'authorization_scope',
            'metadata',
            'user',
        ], name
        args = images_funcs[name].args
        scope_arg = next(a for a in args.args if a.arg == 'authorization_scope')
        scope_idx = args.args.index(scope_arg)
        positional_with_default = len(args.defaults) > (len(args.args) - 1 - scope_idx)
        assert not positional_with_default, f'{name}.authorization_scope must be required'


def test_generate_and_edit_wrappers_removed_feature_gates(images_funcs) -> None:
    for name in ('generate_images', 'edit_images'):
        body = ast.unparse(images_funcs[name])
        assert 'has_permission(' not in body, f'{name} must not consult has_permission'
        assert 'ENABLE_IMAGE_GENERATION' not in body
        assert 'ENABLE_IMAGE_EDIT' not in body


def test_generate_wrapper_passes_direct_scope(images_funcs) -> None:
    body = ast.unparse(images_funcs['generate_images'])
    assert "image_generations(request, form_data, 'direct'" in body or (
        'image_generations(' in body and "'direct'" in body
    )


def test_edit_wrapper_passes_direct_scope(images_funcs) -> None:
    body = ast.unparse(images_funcs['edit_images'])
    assert "image_edits(request, form_data, 'direct'" in body or ('image_edits(' in body and "'direct'" in body)


def test_entry_points_enforce_gate_with_slot_opt_out(images_funcs) -> None:
    """复盘 P0-3：限流/并发门禁必须挂在 image_generations/image_edits 汇合点上。

    chat 中间件、内置工具与 edit 直连端点此前完全绕过门禁；下沉后所有路径
    默认经过包装器，仅异步任务运行器可通过 kw-only 参数声明槽位已由提交端
    持有而跳过（避免双重占用）。
    """
    for wrapper, core in (
        ('image_generations', '_image_generations_core'),
        ('image_edits', '_image_edits_core'),
    ):
        func = images_funcs[wrapper]
        kwonly = dict(zip((arg.arg for arg in func.args.kwonlyargs), func.args.kw_defaults))
        assert 'concurrency_slot_held_by_caller' in kwonly, wrapper
        default = kwonly['concurrency_slot_held_by_caller']
        assert isinstance(default, ast.Constant) and default.value is False, wrapper
        body = ast.unparse(func)
        for call in _GATE_CALLS:
            assert call in body, (wrapper, call)
        assert f'await {core}(' in body, wrapper
        # 跳过分支必须直接走 core，不得重复占用槽位。
        assert body.index('if concurrency_slot_held_by_caller:') < body.index(f'await {core}(')


def test_core_and_direct_endpoints_do_not_wrap_gate_calls(images_funcs) -> None:
    """门禁只存在于包装器一层：core 函数与直连端点不得重复包装门禁。"""
    for name in (
        '_image_generations_core',
        '_image_edits_core',
        'generate_images',
        'edit_images',
    ):
        body = ast.unparse(images_funcs[name])
        for call in _GATE_CALLS:
            assert call not in body, (name, call)


def test_generation_task_runner_declares_slot_already_held() -> None:
    """异步任务执行路径（image/image-to-image 两处）显式声明槽位已由提交端持有。"""
    funcs = _func_defs(_load(_GENERATION_TASKS_PATH))
    body = ast.unparse(funcs['_invoke_generation_provider'])
    assert "'concurrency_slot_held_by_caller': True" in body
    assert 'image_edits(' in body
    assert 'image_generations(' in body


def test_generation_invoke_closure_ignores_prepared_and_uses_provider_form(images_funcs) -> None:
    body = ast.unparse(images_funcs['_image_generations_core'])
    assert '_invoke_image_generations(request, provider_form' in body


def test_invoke_edit_creations_factory_orders_reference_snapshots_after_results(images_funcs) -> None:
    factory = images_funcs['invoke_edit_creations_factory']
    body = ast.unparse(factory)
    assert '_invoke_image_edits(' in body
    assert 'decode_prepared_references(prepared)' in body
    assert 'capture_reference_snapshots(' in body
    # 复盘 #10：编辑成功后快照上传失败必须降级为无快照交付（references = ()），
    # 不能整体失败丢弃已生成的付费结果；ImageTerminalPreparationError 通道已移除。
    assert 'ImageTerminalPreparationError' not in body
    assert 'references = ()' in body
    assert 'CapturedImageBatch(' in body
    # reference upload must happen before the batch is constructed
    assert body.index('_invoke_image_edits(') < body.index('capture_reference_snapshots(')
    assert body.index('capture_reference_snapshots(') < body.index('CapturedImageBatch(')


def test_finalize_image_creations_factory_uses_capture_context_signature(images_funcs) -> None:
    factory = images_funcs['finalize_image_creations_factory']
    context_calls = [
        node
        for node in ast.walk(factory)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == 'build_creation_capture_context'
    ]
    assert len(context_calls) == 1
    # 代码新增了 generation_task_id 关键字参数，用于把图片生成关联到任务记录。
    assert {keyword.arg for keyword in context_calls[0].keywords} == {
        'raw_form',
        'prepared',
        'user',
        'usage_id',
        'generation_task_id',
    }


def test_finalize_image_creations_factory_wires_context_and_finalize(images_funcs) -> None:
    factory = images_funcs['finalize_image_creations_factory']
    body = ast.unparse(factory)
    assert 'build_creation_capture_context(' in body
    assert 'finalize_created_images(' in body


def test_invoke_image_generations_branches_return_captured_batch(images_funcs) -> None:
    invoke = images_funcs['_invoke_image_generations']
    assert _returns_constructor_named(invoke, 'CapturedImageBatch')


def test_invoke_image_edits_branches_return_captured_batch(images_funcs) -> None:
    invoke = images_funcs['_invoke_image_edits']
    assert _returns_constructor_named(invoke, 'CapturedImageBatch')


def test_fal_generation_gates_mock_by_admin_toggle_and_uploads_results(images_funcs) -> None:
    # 复盘 P2：fal 管线属于独立扩展桥接层（generations/edits 共享）。
    invoke = ast.unparse(images_funcs['_invoke_image_generations'])
    bridge_funcs = _func_defs(_load(_FAL_BRIDGE_PATH))
    pipeline = ast.unparse(bridge_funcs['run_fal_image_pipeline'])
    capture = ast.unparse(bridge_funcs['capture_fal_image_result'])
    assert 'run_fal_image_pipeline(' in invoke
    assert 'api_key=image_config.FAL_API_KEY' in invoke
    assert 'if mock_enabled:' in pipeline
    assert 'result = get_mock_fal_image_result(fal_model, form_data)' in pipeline
    assert 'result = await run_fal_queue(' in pipeline
    assert 'capture_fal_image_result(' in pipeline
    assert 'extract_fal_image_urls(result)' in capture
    assert 'download_image(image_url)' in capture
    assert 'upload_image(' in capture
    assert 'cleanup_uploaded_files(uploaded_files)' in capture
    assert 'CapturedImageResult(' in capture
    assert 'ReusedImageResult(' not in invoke
    assert 'ReusedImageResult(' not in pipeline


def test_fal_edit_gates_mock_by_admin_toggle_and_uploads_results(images_funcs) -> None:
    # 复盘 P2：fal 管线提取至独立扩展桥接层；edit 专属差异在
    # 调用点（模型解析、参考图 URL、编辑专用 API key 回退）。
    invoke = ast.unparse(images_funcs['_invoke_image_edits'])
    bridge_funcs = _func_defs(_load(_FAL_BRIDGE_PATH))
    pipeline = ast.unparse(bridge_funcs['run_fal_image_pipeline'])
    capture = ast.unparse(bridge_funcs['capture_fal_image_result'])
    assert 'run_fal_image_pipeline(' in invoke
    assert 'api_key=image_config.IMAGES_EDIT_FAL_API_KEY or image_config.FAL_API_KEY' in invoke
    assert 'if mock_enabled:' in pipeline
    assert 'result = get_mock_fal_image_result(fal_model, form_data)' in pipeline
    assert 'result = await run_fal_queue(' in pipeline
    assert 'capture_fal_image_result(' in pipeline
    assert 'extract_fal_image_urls(result)' in capture
    assert 'download_image(image_url)' in capture
    assert 'upload_image(' in capture
    assert 'CapturedImageResult(' in capture


def test_real_provider_branches_project_captured_image_result(images_funcs) -> None:
    for name in ('_invoke_image_generations', '_invoke_image_edits'):
        body = ast.unparse(images_funcs[name])
        assert 'CapturedImageResult(' in body
        assert 'file_item.id' in body
        assert 'file_item.user_id' in body
        assert 'file_item.created_at' in body


def test_images_module_imports_creation_bridge_symbols(images_tree) -> None:
    source = ast.unparse(images_tree)
    for symbol in (
        'CapturedImageBatch',
        'CapturedImageResult',
        'build_creation_capture_context',
        'capture_reference_snapshots',
        'decode_prepared_references',
        'finalize_created_images',
    ):
        assert symbol in source, f'images.py must import {symbol}'


def test_middleware_passes_chat_scope() -> None:
    source = _MIDDLEWARE_PATH.read_text(encoding='utf-8')
    assert source.count("authorization_scope='chat'") >= 2


def test_builtin_tools_pass_tool_scope() -> None:
    source = _BUILTIN_PATH.read_text(encoding='utf-8')
    assert source.count("authorization_scope='tool'") >= 2


def test_middleware_and_builtin_do_not_supply_direct_scope() -> None:
    middleware = _MIDDLEWARE_PATH.read_text(encoding='utf-8')
    builtin = _BUILTIN_PATH.read_text(encoding='utf-8')
    assert "authorization_scope='direct'" not in middleware
    assert "authorization_scope='direct'" not in builtin
