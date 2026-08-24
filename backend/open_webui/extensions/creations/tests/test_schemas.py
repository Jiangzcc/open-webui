from __future__ import annotations

import pytest
from open_webui.extensions.creations.schemas import (
    CaptionUpdateForm,
    CapturedImageBatch,
    CapturedImageResult,
    CapturedReferenceResult,
    CreationReference,
    CreationSummary,
    ReusedImageResult,
    decode_keyset_cursor,
    encode_keyset_cursor,
)
from pydantic import ValidationError


def test_cursor_round_trip_is_versioned_and_opaque() -> None:
    encoded = encode_keyset_cursor(1_784_680_000, 'creation-9')
    assert '=' not in encoded
    assert decode_keyset_cursor(encoded) == (1_784_680_000, 'creation-9')


def test_cursor_rejects_negative_timestamp_and_non_alphabet_characters() -> None:
    with pytest.raises(ValueError):
        encode_keyset_cursor(-1, 'creation-1')

    encoded = encode_keyset_cursor(1, 'creation-1')
    with pytest.raises(ValueError, match='invalid cursor'):
        decode_keyset_cursor(f'{encoded}!')


@pytest.mark.parametrize('cursor', ['', 'not-base64', 'e30', 'eyJ2IjoyfQ'])
def test_invalid_cursor_is_rejected(cursor: str) -> None:
    with pytest.raises(ValueError, match='invalid cursor'):
        decode_keyset_cursor(cursor)


def test_caption_trims_blank_and_limits_unicode_code_points() -> None:
    assert CaptionUpdateForm(caption='   ').caption is None
    assert CaptionUpdateForm(caption='  备注  ').caption == '备注'
    with pytest.raises(ValidationError):
        CaptionUpdateForm(caption='图' * 1001)


def test_internal_capture_values_are_immutable_and_ordered() -> None:
    reference = CapturedReferenceResult(
        file_id='reference-1',
        file_user_id='user-1',
        file_created_at=10,
        mime_type='image/png',
        sha256='a' * 64,
        position=0,
    )
    batch = CapturedImageBatch(
        images=(
            CapturedImageResult(
                url='/api/v1/files/result-1/content',
                file_id='result-1',
                file_user_id='user-1',
                file_created_at=11,
                mime_type='image/png',
            ),
        ),
        references=(reference,),
    )
    assert batch.references == (reference,)
    with pytest.raises(AttributeError):
        batch.references = ()


def test_reused_result_is_a_distinct_server_only_type() -> None:
    batch = CapturedImageBatch(images=(ReusedImageResult(url='/api/v1/files/old/content'),))
    assert isinstance(batch.images[0], ReusedImageResult)


def test_user_summary_never_accepts_internal_file_identity() -> None:
    payload = {
        'id': 'creation-1',
        'kind': 'image',
        'content_url': '/api/v1/files/result-1/content',
        'availability': 'available',
        'mime_type': 'image/png',
        'caption': None,
        'prompt_preview': 'a calm river',
        'model_name': 'Model',
        'task': 'text-to-image',
        'created_at': 10,
        'updated_at': 10,
        'file_id': 'must-not-survive',
    }
    with pytest.raises(ValidationError):
        CreationSummary.model_validate(payload)


def test_reference_dto_contains_url_state_but_no_internal_id() -> None:
    reference = CreationReference(position=0, content_url=None, availability='missing', mime_type=None)
    assert reference.model_dump() == {
        'position': 0,
        'content_url': None,
        'availability': 'missing',
        'mime_type': None,
    }
