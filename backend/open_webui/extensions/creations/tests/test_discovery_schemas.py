from __future__ import annotations

import pytest
from open_webui.extensions.creations.schemas import PublishCreationForm
from pydantic import ValidationError


def test_publish_form_normalizes_optional_text() -> None:
    form = PublishCreationForm.model_validate(
        {'title': '  Northern lights  ', 'description': '  A quiet night.  ', 'show_prompt': False}
    )

    assert form.title == 'Northern lights'
    assert form.description == 'A quiet night.'
    assert form.show_prompt is False


def test_publish_form_turns_blank_text_into_none_and_defaults_to_show_prompt() -> None:
    form = PublishCreationForm.model_validate({'title': ' ', 'description': '\n'})

    assert form.title is None
    assert form.description is None
    assert form.show_prompt is True


def test_publish_form_rejects_extra_fields_and_oversized_title() -> None:
    with pytest.raises(ValidationError):
        PublishCreationForm.model_validate({'title': 'x', 'creation_id': 'other'})
    with pytest.raises(ValidationError):
        PublishCreationForm.model_validate({'title': 'x' * 201})
