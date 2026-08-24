from open_webui.extensions.fal_catalog.video_schemas import FalVideoModelDefinition


def video_definition(**changes) -> FalVideoModelDefinition:
    values = {
        'id': 'fal-ai/model',
        'public_id': 'model',
        'name': 'Model',
        'provider': 'fal',
        'task': 'text-to-video',
    }
    values.update(changes)
    return FalVideoModelDefinition(**values)


__all__ = ['video_definition']
