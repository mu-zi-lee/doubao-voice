"""执行端：根据 mode 执行覆盖或还原式粘贴。"""
import time
from typing import Literal

import pyautogui
import pyperclip

MODE_OVERWRITE: Literal["overwrite"] = "overwrite"
MODE_RESTORE: Literal["restore"] = "restore"
PASTE_DELAY_SEC = 0.5
RESTORE_DELAY_SEC = 0.1


def paste_executor(text: str, mode: str = MODE_RESTORE) -> None:
    """
    执行粘贴逻辑。
    mode: "overwrite" 直接覆盖粘贴；"restore" 备份剪贴板 -> 写入 -> Ctrl+V -> 还原。
    """
    if not text:
        return

    time.sleep(PASTE_DELAY_SEC)

    if mode == MODE_RESTORE:
        old_content = pyperclip.paste()
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(RESTORE_DELAY_SEC)
        pyperclip.copy(old_content)
    else:
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
