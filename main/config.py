"""中继配置：历史条数等。"""
import os

HISTORY_SIZE = int(os.environ.get("RELAY_HISTORY_SIZE", "10"))
