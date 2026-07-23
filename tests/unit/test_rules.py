from __future__ import annotations

from data_xray_local.domain.models import DataCategory
from data_xray_local.domain.rules import Detector, mask_value


def test_detector_finds_required_transparent_rules() -> None:
    text = """
    Contact avery.north@example.com or +1 (202) 555-0147.
    Ship to 1847 Example Street, Apt 5B.
    Records: 899-12-3456 and 990000199001010018.
    aws_access_key = AKIAIOSFODNN7EXAMPLE
    github_token = ghp_000000000000000000000000000000000000
    Use test card 4111 1111 1111 1111.
    """
    matches = Detector().detect(text)
    categories = {match.category for match in matches}

    assert {
        DataCategory.EMAIL,
        DataCategory.PHONE,
        DataCategory.ADDRESS,
        DataCategory.GOVERNMENT_ID,
        DataCategory.TOKEN,
        DataCategory.PAYMENT_CARD,
    }.issubset(categories)
    assert all(match.raw_value not in match.masked_fragment for match in matches)
    assert all("line " in match.location and "column " in match.location for match in matches)


def test_detector_rejects_repeated_digit_phone_and_invalid_card() -> None:
    matches = Detector().detect("Noise 111-111-1111 and invalid card 4111 1111 1111 1112")
    assert not any(match.category == DataCategory.PHONE for match in matches)
    assert not any(match.category == DataCategory.PAYMENT_CARD for match in matches)


def test_masking_keeps_only_useful_fragments() -> None:
    assert mask_value(DataCategory.EMAIL, "a@example.com") == "a•••@e•••.com"
    assert mask_value(DataCategory.PHONE, "+1 202 555 0147") == "•••-•••-0147"
    assert "1847 Example Street" not in mask_value(DataCategory.ADDRESS, "1847 Example Street")
    assert mask_value(DataCategory.PAYMENT_CARD, "4111111111111111").endswith("1111")
    assert mask_value(DataCategory.GPS_LOCATION, "31.2,121.4") == "[precise location hidden]"


def test_detector_locations_respect_chunk_prefix() -> None:
    match = Detector().detect("avery.north@example.com", "sheet Contacts · B2")[0]
    assert match.location.startswith("sheet Contacts · B2")
