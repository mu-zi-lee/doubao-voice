"""测试 main.config：历史条数配置。"""
import pytest

from main.config import HISTORY_SIZE


def test_history_size_is_positive_int():
    assert isinstance(HISTORY_SIZE, int)
    assert HISTORY_SIZE >= 1
