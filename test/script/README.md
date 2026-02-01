# script 测试说明

油猴脚本在浏览器中运行，无法在 Python 环境内直接单元测试。

- **手动测试**：在 Tampermonkey 中安装 `script/doubao-collector.user.js`，打开豆包对话页，触发一条含代码块的回复，确认控制台有「发送成功」且本地中继收到请求。
- **选择器验证**：豆包正文代码块位于 `[data-testid="message_text_content"] pre code`，兜底为 `pre code` 最后一项。
