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
    gen_params = [a.arg for a in images_funcs['image_generations'].args.args]
    edit_params = [a.arg for a in images_funcs['image_edits'].args.args]
    assert gen_params == ['request', 'form_data', 'authorization_scope', 'metadata', 'user']
    assert edit_params == ['request', 'form_data', 'authorization_scope', 'metadata', 'user']
    for name in ('image_generations', 'image_edits'):
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


def test_generation_invoke_closure_ignores_prepared_and_uses_provider_form(images_funcs) -> None:
    body = ast.unparse(images_funcs['image_generations'])
    assert '_invoke_image_generations(request, provider_form' in body


def test_invoke_edit_creations_factory_orders_reference_snapshots_after_results(images_funcs) -> None:
    factory = images_funcs['invoke_edit_creations_factory']
    body = ast.unparse(factory)
    assert '_invoke_image_edits(' in body
    assert 'decode_prepared_references(prepared)' in body
    assert 'capture_reference_snapshots(' in body
    assert 'ImageTerminalPreparationError' in body
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
    assert {keyword.arg for keyword in context_calls[0].keywords} == {
        'raw_form',
        'prepared',
        'user',
        'usage_id',
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


def test_fal_generation_mock_uses_provider_shaped_urls_and_uploads_results(images_funcs) -> None:
    body = ast.unparse(images_funcs['_invoke_image_generations'])
    assert 'mock_res = get_mock_fal_image_result(fal_model, form_data)' in body
    assert 'res = mock_res' in body
    assert 'res = await run_fal_queue(' in body
    assert 'extract_fal_image_urls(res)' in body
    assert 'get_image_data(image_url)' in body
    assert 'upload_image(' in body
    assert 'CapturedImageResult(' in body
    assert 'ReusedImageResult(' not in body


def test_fal_edit_mock_uses_provider_shaped_urls_and_uploads_results(images_funcs) -> None:
    body = ast.unparse(images_funcs['_invoke_image_edits'])
    assert 'mock_res = get_mock_fal_image_result(edit_model, form_data)' in body
    assert 'res = mock_res' in body
    assert 'res = await run_fal_queue(' in body
    assert 'extract_fal_image_urls(res)' in body
    assert 'get_image_data(image_url)' in body
    assert 'upload_image(' in body
    assert 'CapturedImageResult(' in body


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
