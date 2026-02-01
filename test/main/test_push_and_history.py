"""测试 main.relay：/api/push、/api/history 及 executor 调用。"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main.relay import app, history_queue

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_history():
    history_queue.clear()
    yield
    history_queue.clear()


@patch("main.relay._get_paste_executor")
def test_push_received_and_history(mock_get_executor):
    mock_executor = MagicMock()
    mock_get_executor.return_value = mock_executor

    payload = {"content": "hello world", "timestamp": 1234567890, "mode": "restore"}
    resp = client.post("/api/push", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "received"}

    hist = client.get("/api/history").json()
    assert len(hist) == 1
    assert hist[0]["content"] == "hello world"
    assert hist[0]["timestamp"] == 1234567890
    assert hist[0]["mode"] == "restore"

    mock_executor.assert_called_once_with("hello world", "restore")


@patch("main.relay._get_paste_executor")
def test_push_default_mode(mock_get_executor):
    mock_executor = MagicMock()
    mock_get_executor.return_value = mock_executor

    resp = client.post(
        "/api/push",
        json={"content": "foo", "timestamp": 1},
    )
    assert resp.status_code == 200
    hist = client.get("/api/history").json()
    assert hist[0]["mode"] == "restore"
    mock_executor.assert_called_once_with("foo", "restore")


@patch("main.relay._get_paste_executor")
def test_push_overwrite_mode(mock_get_executor):
    mock_executor = MagicMock()
    mock_get_executor.return_value = mock_executor

    resp = client.post(
        "/api/push",
        json={"content": "bar", "timestamp": 2, "mode": "overwrite"},
    )
    assert resp.status_code == 200
    mock_executor.assert_called_once_with("bar", "overwrite")
