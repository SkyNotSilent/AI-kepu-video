"""
数据库模块初始化
本地开发模式：使用 SQLite + 内存缓存
"""

import os

if os.environ.get("USE_REMOTE_DB") == "1":
    from .mysql_client import mysql_client, MySQLClient
    from .redis_client import redis_client, RedisClient
else:
    from .sqlite_client import sqlite_client as mysql_client, SQLiteClient as MySQLClient
    from .memory_cache import memory_cache as redis_client, MemoryCache as RedisClient

__all__ = ["mysql_client", "MySQLClient", "redis_client", "RedisClient"]
