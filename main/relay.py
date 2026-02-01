"""中继：接收 push、维护历史、后台调用执行端。"""
from collections import deque

from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel

from main.config import HISTORY_SIZE

# 延迟导入，便于测试时 mock
def _get_paste_executor():
    from executor.executor import paste_executor
    return paste_executor


app = FastAPI(title="doubao-voice relay")
history_queue: deque = deque(maxlen=HISTORY_SIZE)


class PushMessage(BaseModel):
    content: str
    timestamp: int
    mode: str = "restore"


@app.post("/api/push")
async def receive_content(msg: PushMessage, background_tasks: BackgroundTasks):
    record = msg.model_dump()
    history_queue.append(record)
    paste_executor = _get_paste_executor()
    background_tasks.add_task(paste_executor, msg.content, msg.mode)
    return {"status": "received"}


@app.get("/api/history")
async def get_history():
    return list(history_queue)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
