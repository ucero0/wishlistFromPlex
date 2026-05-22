from app.adapters.http.mappers.disk_size_format import format_bytes_for_display


def test_format_bytes_none():
    assert format_bytes_for_display(None) is None


def test_format_bytes_gigabytes():
    assert format_bytes_for_display(944_189_378_560) == "879.42 GB"


def test_format_bytes_terabytes():
    assert format_bytes_for_display(1_081_101_176_832) == "1.01 TB"


def test_format_bytes_small():
    assert format_bytes_for_display(512) == "512 B"
