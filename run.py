"""单 exe 入口：启动中继（含管理页静态）。"""
if __name__ == "__main__":
    import uvicorn
    from main.relay import app
    uvicorn.run(app, host="127.0.0.1", port=8000)
