"""中继：接收 push、维护历史、后台调用执行端，挂载管理页静态。"""
import sys
from pathlib import Path
from collections import deque

from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from main.config import (
    HISTORY_SIZE,
    load_config,
    save_config,
    load_history,
    save_history,
    load_prompts,
    save_prompts,
    get_ai_optimize_enabled,
)


def _get_web_static_dir() -> Path | None:
    """开发时为项目根下 web/；打包后为 _MEIPASS 下 web。"""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    path = base / "web"
    return path if path.is_dir() else None


def _get_paste_executor():
    from executor.executor import paste_executor
    return paste_executor


def _get_optimizer():
    from ai_opt.optimizer import optimize
    return optimize


app = FastAPI(title="豆言 relay")
history_queue: deque = deque(maxlen=HISTORY_SIZE)
for record in load_history(HISTORY_SIZE):
    history_queue.append(record)


class PushMessage(BaseModel):
    content: str
    timestamp: int
    mode: str = "restore"


class ConfigBody(BaseModel):
    history_size: int = Field(ge=1, le=1000, description="历史条数")
    ai_optimize_enabled: bool = False
    default_mode: str = Field(pattern="^(restore|overwrite)$")
    ai_api_key: str = ""
    ai_base_url: str = ""


@app.post("/api/push")
async def receive_content(msg: PushMessage, background_tasks: BackgroundTasks):
    record = msg.model_dump()
    history_queue.append(record)
    save_history(list(history_queue))
    content = msg.content
    if get_ai_optimize_enabled():
        content = _get_optimizer()(content)
    paste_executor = _get_paste_executor()
    background_tasks.add_task(paste_executor, content, msg.mode)
    return {"status": "received"}


@app.get("/api/history")
async def get_history():
    return list(history_queue)


@app.get("/api/config")
async def api_get_config():
    return load_config()


@app.put("/api/config")
async def api_put_config(body: ConfigBody):
    save_config(body.model_dump())
    return load_config()


@app.get("/api/prompts")
async def api_get_prompts():
    return load_prompts()


@app.put("/api/prompts")
async def api_put_prompts(body: dict[str, str]):
    save_prompts(body)
    return load_prompts()


web_dir = _get_web_static_dir()
if web_dir is not None:
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")
    index_path = web_dir / "index.html"

    @app.get("/")
    @app.get("/dashboard")
    async def serve_index():
        if index_path.exists():
            return FileResponse(index_path)
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse("index.html not found", status_code=404)
