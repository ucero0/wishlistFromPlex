from app.core.formatting import format_bytes_for_display


def test_format_bytes_none():
    assert format_bytes_for_display(None) is None


def test_format_bytes_gigabytes():
    assert format_bytes_for_display(944_189_378_560) == "879.34 GB"


def test_format_bytes_terabytes():
    assert format_bytes_for_display(1_099_511_627_776) == "1.00 TB"


def test_format_bytes_small():
    assert format_bytes_for_display(512) == "512 B"
