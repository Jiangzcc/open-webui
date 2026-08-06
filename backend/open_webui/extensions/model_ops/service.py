from __future__ import annotations

from time import time

from fastapi import HTTPException
from open_webui.extensions.fal_catalog.loader import load_image_catalog
from open_webui.utils.images.fal_models import normalize_fal_image_model_id
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ImageModelOperation
from .schemas import ModelOperationItem, ModelOperationList, ModelOperationUpdate


def _tags(row: ImageModelOperation | None) -> tuple[str, ...]:
    value = row.tags_json if row is not None else []
    return tuple(item for item in value if isinstance(item, str)) if isinstance(value, list) else ()


async def _operation_map(session: AsyncSession) -> dict[str, ImageModelOperation]:
    rows = (await session.scalars(select(ImageModelOperation))).all()
    return {row.model_id: row for row in rows}


async def apply_model_operations(
    session: AsyncSession,
    models: list[dict[str, object]],
    *,
    admin: bool,
) -> list[dict[str, object]]:
    operations = await _operation_map(session)
    decorated: list[tuple[int, dict[str, object]]] = []
    for index, model in enumerate(models):
        candidate = model.get('id')
        internal_id = normalize_fal_image_model_id(candidate if isinstance(candidate, str) else None)
        operation = operations.get(internal_id or '')
        visible = operation.visible if operation is not None else True
        enabled = operation.enabled if operation is not None else True
        # Hidden models are omitted from the public catalog. Disabled models stay
        # visible so users can read the maintenance explanation, while
        # ensure_model_enabled remains the server-side enforcement boundary.
        if not admin and not visible:
            continue
        item = {
            **model,
            'visible': visible,
            'enabled': enabled,
            'recommended': operation.recommended if operation is not None else False,
            'sort_order': operation.sort_order if operation is not None else 1000,
            'tags': list(_tags(operation)),
            'maintenance_message': operation.maintenance_message if operation is not None else None,
        }
        decorated.append((index, item))
    decorated.sort(
        key=lambda pair: (
            not bool(pair[1]['recommended']),
            int(pair[1]['sort_order']),
            pair[0],
        )
    )
    return [item for _, item in decorated]


async def ensure_model_enabled(session: AsyncSession, model_id: str | None) -> None:
    internal_id = normalize_fal_image_model_id(model_id)
    if internal_id is None:
        return
    operation = await session.get(ImageModelOperation, internal_id)
    if operation is not None and not operation.enabled:
        raise HTTPException(
            status_code=503,
            detail={
                'code': 'image_model_unavailable',
                'message': operation.maintenance_message,
            },
        )


async def list_model_operations(session: AsyncSession) -> ModelOperationList:
    operations = await _operation_map(session)
    items = []
    for definition in load_image_catalog().definitions:
        operation = operations.get(definition.id)
        items.append(
            ModelOperationItem(
                model_id=definition.id,
                public_id=definition.public_id,
                name=definition.name,
                provider=definition.provider,
                task=definition.task,
                visible=operation.visible if operation is not None else True,
                enabled=operation.enabled if operation is not None else True,
                recommended=operation.recommended if operation is not None else False,
                sort_order=operation.sort_order if operation is not None else 1000,
                tags=_tags(operation),
                maintenance_message=operation.maintenance_message if operation is not None else None,
                updated_at=operation.updated_at if operation is not None else None,
            )
        )
    items.sort(key=lambda item: (not item.recommended, item.sort_order, item.provider, item.name))
    return ModelOperationList(items=tuple(items))


async def update_model_operation(
    session: AsyncSession,
    model_id: str,
    form: ModelOperationUpdate,
    operator: object,
) -> ModelOperationItem | None:
    internal_id = normalize_fal_image_model_id(model_id)
    if internal_id is None:
        return None
    catalog = load_image_catalog()
    definition = next((item for item in catalog.definitions if item.id == internal_id), None)
    if definition is None:
        return None
    row = await session.get(ImageModelOperation, internal_id)
    if row is None:
        row = ImageModelOperation(
            model_id=internal_id,
            visible=True,
            enabled=True,
            recommended=False,
            sort_order=1000,
            tags_json=[],
            maintenance_message=None,
            updated_at=int(time()),
        )
        session.add(row)
    changes = form.model_dump(exclude_unset=True)
    if 'tags' in changes:
        row.tags_json = list(changes.pop('tags') or ())
    for field, value in changes.items():
        setattr(row, field, value)
    row.updated_by_id = getattr(operator, 'id', None)
    row.updated_by_name_snapshot = getattr(operator, 'name', None)
    row.updated_at = int(time())
    await session.commit()
    return ModelOperationItem(
        model_id=definition.id,
        public_id=definition.public_id,
        name=definition.name,
        provider=definition.provider,
        task=definition.task,
        visible=row.visible,
        enabled=row.enabled,
        recommended=row.recommended,
        sort_order=row.sort_order,
        tags=_tags(row),
        maintenance_message=row.maintenance_message,
        updated_at=row.updated_at,
    )


__all__ = [
    'apply_model_operations',
    'ensure_model_enabled',
    'list_model_operations',
    'update_model_operation',
]
