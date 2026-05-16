from upv_gym_booking.config import parse_bool, parse_session_codes


def test_parse_session_codes_accepts_mixed_formats() -> None:
    assert parse_session_codes("9, MUS024;039,009") == ("009", "024", "039")


def test_parse_bool_uses_default_for_missing_values() -> None:
    assert parse_bool(None, default=True) is True
    assert parse_bool("", default=False) is False
    assert parse_bool("false", default=True) is False
    assert parse_bool("yes", default=False) is True
