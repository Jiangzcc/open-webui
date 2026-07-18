import asyncio
import json
from types import SimpleNamespace


def test_credit_price_events_map_to_registered_upstream_events(monkeypatch) -> None:
    from open_webui import events
    from open_webui.extensions.credits import compat

    calls = []

    async def publish(_request, event, **kwargs):
        assert events.event_name(event) in events.EVENT_CATALOG_SET
        calls.append((event.name, kwargs))

    monkeypatch.setattr(events, 'publish_event', publish)
    actor = SimpleNamespace(id='admin-1', name='Admin', email='admin@example.test', role='admin')

    for operation, expected_event in (
        ('created', events.EVENTS.MODEL_PROVIDER_MODEL_CREATED.name),
        ('updated', events.EVENTS.MODEL_PROVIDER_CONFIG_UPDATED.name),
        ('deleted', events.EVENTS.MODEL_PROVIDER_MODEL_DELETED.name),
    ):
        asyncio.run(
            compat.publish_credit_price_event(
                object(),
                operation,
                actor=actor,
                subject_id='price-1',
                data={'changed_fields': ['rules']},
            )
        )
        event_name, kwargs = calls[-1]
        assert event_name == expected_event
        assert kwargs['subject_type'] == 'credit_price'
        assert kwargs['data'] == {'credit_price_operation': operation, 'changed_fields': ['rules']}
        assert 'secret-rule-text' not in json.dumps(kwargs, default=str)
