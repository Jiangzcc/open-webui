from __future__ import annotations

import pytest
from open_webui.extensions.creations.schemas import (
    DiscoveryCategoryCreateForm,
    DiscoveryCategoryUpdateForm,
    PublishCreationForm,
)
from pydantic import ValidationError


def test_publish_form_normalizes_optional_text() -> None:
    form = PublishCreationForm.model_validate(
        {'title': '  Northern lights  ', 'description': '  A quiet night.  ', 'show_prompt': False}
    )

    assert form.title == 'Northern lights'
    assert form.description == 'A quiet night.'
    assert form.show_prompt is False
    assert form.category is None


def test_publish_form_turns_blank_text_into_none_and_defaults_to_show_prompt() -> None:
    form = PublishCreationForm.model_validate({'title': ' ', 'description': '\n'})

    assert form.title is None
    assert form.description is None
    assert form.show_prompt is True
    assert form.category is None


def test_publish_form_rejects_extra_fields_and_oversized_title() -> None:
    with pytest.raises(ValidationError):
        PublishCreationForm.model_validate({'title': 'x', 'creation_id': 'other'})
    with pytest.raises(ValidationError):
        PublishCreationForm.model_validate({'title': 'x' * 201})


def test_category_update_normalizes_name_and_requires_a_change() -> None:
    form = DiscoveryCategoryUpdateForm.model_validate({'display_name': '  摄影人像  ', 'sort_order': 5})
    assert form.display_name == '摄影人像'
    assert form.sort_order == 5

    with pytest.raises(ValidationError):
        DiscoveryCategoryUpdateForm.model_validate({})
    with pytest.raises(ValidationError):
        DiscoveryCategoryUpdateForm.model_validate({'display_name': '   '})


def test_category_create_normalizes_name_and_defaults() -> None:
    form = DiscoveryCategoryCreateForm.model_validate({'display_name': '  摄影  '})
    assert form.display_name == '摄影'
    assert form.enabled is True
    assert form.sort_order == 1000
