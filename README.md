# 豆言 (doubao-voice)

豆包语音/文字返回内容自动采集并粘贴到本地输入框：油猴采集 → 中继存储与路由 → 执行端粘贴。三层解耦，免去手动复制。

**作者**：木子不是木子狸

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

**管理页**：浏览器访问 `http://127.0.0.1:8000/` 或 `http://127.0.0.1:8000/dashboard` 可管理设置（历史条数、AI 优化开关、AI API Key / Base URL、默认粘贴模式）、查看历史记录、编辑后端提示词。配置、提示词与**历史记录**均持久化在用户目录（Windows `%APPDATA%/doubao-voice/`，Unix `~/.config/doubao-voice/`），重启或刷新后历史会从 `history.json` 恢复。

## 豆包提示词

让豆包把语音转文字放进代码块，便于本工具抓取并粘贴。可将下面提示词复制到豆包对话中作为系统/角色设定使用。**可自行修改提示词**：若希望输出被润色、整理或分段，只需在提示词中说明（并保持「结果放在一个 Markdown 代码块中输出」），本工具仍会抓取代码块内容并粘贴。

```
绝对禁令：禁止输出任何开场白、结束语或自我介绍。
唯一任务：将用户输入的语音转文字内容原封不动地放入一个 Markdown 代码块中输出。
格式：输出有且仅有三行——第一行 ``` ；第二行 [用户内容原文，一字不改] ；第三行 ``` 。禁止对内容做标点修正、分段或排版。
异常：若用户输入为空，不输出任何字符。
```

## 运行与常见情况

### 完整启动流程（简要）

1. **首次**：在项目根执行 `uv sync` 安装依赖。
2. **每次使用前**：在项目根执行 `uv run uvicorn main.relay:app --host 127.0.0.1 --port 8000` 启动中继，保持该终端不关。
3. 浏览器安装 Tampermonkey，添加并启用 `script/doubao-collector.user.js`。
4. 使用：光标放在要输入的输入框 → 打开豆包对话页 → 让豆包输出含代码块的回复 → 内容会自动粘贴到光标处。

### 可能遇到的情况与处理

| 情况 | 原因与处理 |
|------|-------------|
| **Tampermonkey 弹窗：「A userscript wants to access a cross-origin resource」** | 脚本从豆包页面向本地 `http://127.0.0.1:8000` 发请求，属于跨域。**点「允许」/ Allow**，脚本才能把内容发到中继。脚本已声明 `@connect 127.0.0.1`，部分环境下可减少此弹窗。 |
| **脚本状态显示「This script hasn't run yet」** | 当前页面 URL 与脚本的 `@match` 不匹配。脚本仅对 **`https://www.doubao.com/*`** 生效，请确认地址栏是带 `www` 的豆包域名，并在对话页 **整页刷新（F5）** 一次。 |
| **页面出现 403（Failed to load resource）** | 多为豆包站点自身接口或资源返回 403，与本地中继无关。若 403 的请求地址是 `127.0.0.1:8000`，再检查中继是否已启动、端口是否被占用或防火墙拦截。 |
| **中继启动失败或端口被占** | 确保 8000 端口未被其他程序占用；可改用其他端口，例如 `uv run uvicorn main.relay:app --host 127.0.0.1 --port 8001`，并同步修改油猴脚本中的 `RELAY_URL`。 |
| **没有自动粘贴** | 确认：(1) 中继已启动；(2) 油猴脚本已允许访问 127.0.0.1；(3) 光标/焦点在目标输入框内；(4) 豆包回复中确实有代码块（`pre code` 区域）。 |

## 项目结构

```
doubao-voice/
├── .python-version          # uv 使用的 Python 版本（如 3.12）
├── pyproject.toml          # 项目与依赖（uv 管理，与主环境分离）
├── run.py                  # 单 exe 入口（打包用）
├── run.spec                # PyInstaller spec（内嵌 web）
├── main/                   # 中继
│   ├── __init__.py
│   ├── config.py           # 配置、提示词与历史记录持久化（用户目录）
│   ├── relay.py            # FastAPI：/api/push、/api/history、/api/config、/api/prompts，挂载 web
│   └── requirements.txt
├── executor/               # 执行端
│   ├── __init__.py
│   ├── executor.py         # paste_executor(text, mode)
│   └── requirements.txt
├── ai_opt/                 # AI 优化（粘贴前对内容优化，当前为 stub）
│   ├── __init__.py
│   └── optimizer.py       # optimize(text) -> str
├── web/                    # 管理页（纯静态）
│   ├── index.html
│   ├── style.css
│   └── app.js
├── script/
│   └── doubao-collector.user.js   # 油猴：豆包代码块 → POST 中继
├── test/
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
  默认 `mode=restore`。若设置中启用 AI 优化，会先对 content 做优化再粘贴。返回 `{ "status": "received" }`。

- **GET /api/history**  
  返回最近 N 条记录（N 由设置中的历史条数决定），每项含 `content`、`timestamp`、`mode`。历史持久化在用户目录 `history.json`，重启后自动恢复。

- **GET /api/config**  
  返回当前配置：`history_size`、`ai_optimize_enabled`、`default_mode`。

- **PUT /api/config**  
  Body: `{ "history_size": number, "ai_optimize_enabled": boolean, "default_mode": "restore"|"overwrite", "ai_api_key": string, "ai_base_url": string }`  
  持久化到用户目录；修改历史条数需重启中继生效。`ai_api_key`、`ai_base_url` 供 AI 优化接入真实 API 时使用（可选）。

- **GET /api/prompts**  
  返回后端保存的提示词对象（键值对）。

- **PUT /api/prompts**  
  Body: `{ "键名": "内容", ... }`  
  覆盖保存提示词。

---

## 打包为单 exe

安装开发依赖后，在项目根执行：

```bash
uv sync --all-extras
uv run pyinstaller run.spec
```

产物在 `dist/doubao-voice.exe`（Windows）。exe 内嵌 `web/` 静态；配置、提示词与历史记录均写在用户目录，不依赖 exe 所在路径。双击 exe 即启动中继，浏览器访问 `http://127.0.0.1:8000/` 打开管理页。

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

### 7. 运行说明与常见情况

- **新增** README 小节「运行与常见情况」：完整启动流程（简要四步）；表格列出可能遇到的情况与处理（Tampermonkey 跨域弹窗、脚本未运行、403、端口占用、未自动粘贴等）。
- **脚本** `script/doubao-collector.user.js`：增加 `@connect 127.0.0.1`，便于 Tampermonkey 预声明跨域目标，减少跨域确认弹窗。

### 8. 历史记录持久化

- **更新** `main/config.py`：新增 `history.json` 读写；`load_history(max_size)` 从用户目录读取历史（最多保留 max_size 条），`save_history(records)` 写入当前历史列表。
- **更新** `main/relay.py`：启动时用 `load_history(HISTORY_SIZE)` 填充队列；每次 `POST /api/push` 后调用 `save_history(list(history_queue))` 写回文件。重启或刷新后历史从用户目录恢复。
- **更新** `README.md`：管理页、项目结构、API、打包小节及本实现记录中补充历史持久化说明。

以上为本次实现的全部操作记录。
