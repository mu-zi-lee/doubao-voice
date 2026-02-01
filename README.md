# doubao-voice

豆包语音/文字返回内容自动采集并粘贴到本地输入框：油猴采集 → 中继存储与路由 → 执行端粘贴。三层解耦，免去手动复制。

## 架构

| 部分 | 目录 | 职责 |
|------|------|------|
| 采集 | `script/` | 油猴脚本：监听豆包页面代码块，提取并 POST 到中继 |
| 中继 | `main/` | FastAPI：接收 push、维护历史队列、后台调用执行端 |
| 执行 | `executor/` | Python：按 mode 覆盖或还原剪贴板并 Ctrl+V |

- **历史条数**：由环境变量 `RELAY_HISTORY_SIZE` 控制（默认 10）。
- **粘贴模式**：由前端/油猴在 `POST /api/push` 中传 `mode`：`overwrite` 直接粘贴，`restore` 备份剪贴板 → 粘贴 → 还原。

## 环境与依赖

- **uv**：用于运行与依赖管理，与系统 Python 隔离（不依赖本机已安装的 Python/pip）。
- 浏览器安装 Tampermonkey

在项目根目录使用 uv 创建虚拟环境并安装依赖（仅首次或依赖变更时）：

```bash
uv sync
```

之后所有运行均通过 `uv run`，保证在项目虚拟环境中执行：

```bash
# 启动中继
uv run uvicorn main.relay:app --host 127.0.0.1 --port 8000

# 运行测试
uv run pytest test/ -v
```

## 使用步骤

1. **启动中继**：在项目根执行 `uv run uvicorn main.relay:app --host 127.0.0.1 --port 8000`。
2. **安装油猴脚本**：在 Tampermonkey 中新建脚本，粘贴 `script/doubao-collector.user.js` 保存。
3. **使用**：在需要输入的输入框点一下（光标就位），打开豆包对话页，让豆包输出含代码块的回复；脚本会自动抓取最新代码块发到中继，执行端会粘贴到当前焦点位置。

历史记录：浏览器访问 `http://127.0.0.1:8000/api/history` 查看最近推送内容。

## 项目结构

```
doubao-voice/
├── .python-version          # uv 使用的 Python 版本（如 3.12）
├── pyproject.toml           # 项目与依赖（uv 管理，与主环境分离）
├── main/                    # 中继
│   ├── __init__.py
│   ├── config.py            # HISTORY_SIZE 等配置
│   ├── relay.py             # FastAPI：/api/push、/api/history
│   └── requirements.txt
├── executor/                # 执行端
│   ├── __init__.py
│   ├── executor.py          # paste_executor(text, mode)
│   └── requirements.txt
├── script/
│   └── doubao-collector.user.js   # 油猴：豆包代码块 → POST 中继
├── test/                    # 按模块分子目录
│   ├── main/
│   │   ├── test_config.py
│   │   └── test_push_and_history.py
│   ├── executor/
│   │   └── test_paste_executor.py
│   └── script/
│       └── README.md
└── README.md
```

## 测试

在项目根目录执行（使用 uv 以保证环境一致）：

```bash
uv run pytest test/ -v
```

- `test/main/`：中继 push/history 与对 executor 的调用（mock executor）。
- `test/executor/`：paste_executor 的 restore/overwrite 行为（mock pyperclip/pyautogui）。
- `test/script/`：见 `test/script/README.md`，油猴脚本建议手动或 E2E 验证。

## API

- **POST /api/push**  
  Body: `{ "content": string, "timestamp": number, "mode"?: "overwrite"|"restore" }`  
  默认 `mode=restore`。返回 `{ "status": "received" }`。

- **GET /api/history**  
  返回最近 N 条记录（N 由 `RELAY_HISTORY_SIZE` 决定），每项含 `content`、`timestamp`、`mode`。

---

## 实现记录（Changelog）

以下为本次实现过程中所做的操作与文件变更，均记录在此 README。

### 1. 中继模块 `main/`

- **新增** `main/__init__.py`：包标识。
- **新增** `main/config.py`：从环境变量 `RELAY_HISTORY_SIZE` 读取历史条数，默认 10。
- **新增** `main/relay.py`：FastAPI 应用；`POST /api/push` 接收 content/timestamp/mode，写入 deque 并后台调用 `executor.paste_executor(content, mode)`；`GET /api/history` 返回队列列表。
- **新增** `main/requirements.txt`：fastapi、uvicorn。

### 2. 执行端 `executor/`

- **新增** `executor/__init__.py`：导出 `paste_executor`。
- **新增** `executor/executor.py`：`paste_executor(text, mode)`，支持 `restore`（备份剪贴板→粘贴→还原）与 `overwrite`（直接覆盖粘贴）；依赖 pyperclip、pyautogui。
- **新增** `executor/requirements.txt`：pyautogui、pyperclip。

### 3. 采集端 `script/`

- **新增** `script/doubao-collector.user.js`：Tampermonkey 脚本；使用 `MutationObserver` 监听 DOM；优先选择器 `[data-testid="message_text_content"] pre code`，兜底 `pre code`，取最后一项 `innerText`；去重后 POST 到 `http://127.0.0.1:8000/api/push`，body 含 content、timestamp、mode（默认 `restore`）。

### 4. 测试 `test/`

- **新增** `test/__init__.py`、`test/main/__init__.py`、`test/executor/__init__.py`、`test/script/__init__.py`：测试包结构（按模块分子目录）。
- **新增** `test/main/test_config.py`：断言 `main.config.HISTORY_SIZE` 为正整数。
- **新增** `test/main/test_push_and_history.py`：使用 FastAPI TestClient；mock `_get_paste_executor`；测试 POST /api/push 返回 200、GET /api/history 含记录、executor 被以正确 (content, mode) 调用；测试默认 mode 与 overwrite mode。
- **新增** `test/executor/test_paste_executor.py`：mock pyperclip、pyautogui、time.sleep；测试 restore 时 paste 一次、copy 两次、hotkey 一次；测试 overwrite 时 copy 一次、hotkey 一次；测试空字符串不调用 copy/hotkey。
- **新增** `test/script/README.md`：说明油猴脚本需在浏览器中手动或 E2E 验证，并注明豆包代码块选择器。

### 5. 根目录

- **新增** `requirements.txt`：汇总 main、executor、pytest、httpx 等依赖，便于从项目根一键安装并运行/测试。
- **更新** `README.md`：补充架构说明、环境与依赖、使用步骤、项目结构、测试方式、API 说明，以及本实现记录（Changelog）。

### 6. 使用 uv 进行运行管理（与主环境分离）

- **新增** `pyproject.toml`：项目元数据与依赖由 uv 管理；`uv sync` 创建/更新虚拟环境并安装依赖；所有运行通过 `uv run` 在项目环境中执行，与电脑主 Python 环境分离。
- **新增** `.python-version`：指定 uv 使用的 Python 版本（如 3.12）。
- **新增** `.gitignore`：忽略 `.venv/`、`__pycache__/`、`.pytest_cache/` 等。
- **更新** `README.md`：环境与依赖、使用步骤、测试均改为 uv 命令（`uv sync`、`uv run uvicorn ...`、`uv run pytest ...`）；项目结构补充 `pyproject.toml`、`.python-version`；实现记录增加本条目。

以上为本次实现的全部操作记录。
