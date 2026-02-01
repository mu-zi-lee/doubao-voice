"""测试 executor.executor：restore/overwrite 调用顺序。"""
from unittest import mock

from executor.executor import paste_executor


@mock.patch("executor.executor.pyautogui.hotkey")
@mock.patch("executor.executor.pyperclip.copy")
@mock.patch("executor.executor.pyperclip.paste")
@mock.patch("executor.executor.time.sleep")
def test_paste_executor_restore(mock_sleep, mock_paste, mock_copy, mock_hotkey):
    mock_paste.return_value = "old clipboard"
    paste_executor("new text", "restore")

    mock_paste.assert_called_once()
    assert mock_copy.call_count == 2
    mock_copy.assert_any_call("new text")
    mock_copy.assert_any_call("old clipboard")
    mock_hotkey.assert_called_once_with("ctrl", "v")


@mock.patch("executor.executor.pyautogui.hotkey")
@mock.patch("executor.executor.pyperclip.copy")
@mock.patch("executor.executor.pyperclip.paste")
@mock.patch("executor.executor.time.sleep")
def test_paste_executor_overwrite(mock_sleep, mock_paste, mock_copy, mock_hotkey):
    paste_executor("overwrite text", "overwrite")

    mock_paste.assert_not_called()
    mock_copy.assert_called_once_with("overwrite text")
    mock_hotkey.assert_called_once_with("ctrl", "v")


@mock.patch("executor.executor.pyautogui.hotkey")
@mock.patch("executor.executor.pyperclip.copy")
@mock.patch("executor.executor.time.sleep")
def test_paste_executor_empty_no_op(mock_sleep, mock_copy, mock_hotkey):
    paste_executor("", "restore")
    mock_copy.assert_not_called()
    mock_hotkey.assert_not_called()
