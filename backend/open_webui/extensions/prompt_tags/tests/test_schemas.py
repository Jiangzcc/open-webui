from __future__ import annotations

import pytest
from open_webui.extensions.prompt_tags.schemas import (
    PromptTagCategoryUpdate,
    PromptTagCreate,
    PromptTagImportRequest,
    PromptTagModelRef,
    PromptTagUpdate,
)
from pydantic import ValidationError


def test_tag_input_normalizes_text_media_and_model_references() -> None:
    form = PromptTagCreate(
        slug='  cinematic-lighting  ',
        category_id=' category-1 ',
        label_zh=' 电影感  光效 ',
        label_en=' Cinematic   lighting ',
        insert_text=' cinematic\nlighting ',
        media_kinds=('video', 'image', 'video'),
        model_refs=(
            PromptTagModelRef(media_kind='video', model_id=' ltx-2.3 '),
            PromptTagModelRef(media_kind='video', model_id='ltx-2.3'),
        ),
    )

    assert form.slug == 'cinematic-lighting'
    assert form.category_id == 'category-1'
    assert form.label_zh == '电影感 光效'
    assert form.insert_text == 'cinematic lighting'
    assert form.media_kinds == ('video', 'image')
    assert form.model_refs == (PromptTagModelRef(media_kind='video', model_id='ltx-2.3'),)


@pytest.mark.parametrize(
    'payload',
    [
        {'media_kinds': ()},
        {
            'media_kinds': ('image',),
            'model_refs': ({'media_kind': 'video', 'model_id': 'ltx-2.3'},),
        },
    ],
)
def test_tag_input_rejects_invalid_applicability(payload) -> None:
    with pytest.raises(ValidationError):
        PromptTagCreate(
            slug='tag',
            category_id='category',
            label_zh='标签',
            label_en='Tag',
            insert_text='tag text',
            **payload,
        )


def test_patch_forms_require_at_least_one_change() -> None:
    with pytest.raises(ValidationError):
        PromptTagCategoryUpdate()
    with pytest.raises(ValidationError):
        PromptTagUpdate()


def test_import_rejects_duplicates_and_unknown_categories() -> None:
    category = {
        'slug': 'lighting',
        'name_zh': '光影',
        'name_en': 'Lighting',
    }
    with pytest.raises(ValidationError, match='duplicate category slug'):
        PromptTagImportRequest(categories=(category, category), tags=())
    with pytest.raises(ValidationError, match='imported category'):
        PromptTagImportRequest(
            categories=(category,),
            tags=(
                {
                    'slug': 'tag',
                    'category_slug': 'missing',
                    'label_zh': '标签',
                    'label_en': 'Tag',
                    'insert_text': 'tag',
                },
            ),
        )
