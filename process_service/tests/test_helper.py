import pytest

from process_service.src.utils import helper


def test_is_bin_file_true():
    assert helper.is_bin_file("flight.bin") is True


def test_is_bin_file_false():
    assert helper.is_bin_file("flight.txt") is False


def test_is_bin_file_none():
    assert helper.is_bin_file(None) is False


def test_timer_calculate_rounds_duration(monkeypatch):
    monkeypatch.setattr(helper.time, "perf_counter", lambda: 100.75)
    assert helper.timer_calculate(100.0) == 0.75
