from __future__ import annotations

from open_webui.extensions.credits.init_prices import generate_init_script


def test_generated_seed_script_uses_seconds_for_credit_price_timestamps(tmp_path) -> None:
    output_path = tmp_path / 'seed_prices.py'
    generate_init_script(
        [
            {
                'service_type': 'image',
                'resource_id': 'example/model',
                'action': 'text-to-image',
                'base_price': '1',
                'rules': {'schema_version': 1, 'dimensions': []},
            }
        ],
        output_path,
    )

    source = output_path.read_text(encoding='utf-8')
    assert 'now = int(time())' in source
    assert 'now = int(time() * 1000)' not in source
