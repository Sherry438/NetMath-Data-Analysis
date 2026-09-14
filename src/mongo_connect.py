"""
连接 NetMath MongoDB（通过已建立的 SSH tunnel）。

前提：SSH tunnel 已经在本地开着，把远端 MongoDB 转发到本地端口：
    127.0.0.1:27019  ->  SSH tunnel  ->  NetMath MongoDB

用法：
    from src.mongo_connect import get_db
    db = get_db()
    db.list_collection_names()
"""

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

load_dotenv()


def get_client() -> MongoClient:
    host = os.getenv("MONGO_HOST", "127.0.0.1")
    port = os.getenv("MONGO_PORT", "27019")
    user = os.getenv("MONGO_USER", "")
    password = os.getenv("MONGO_PASSWORD", "")
    auth_source = os.getenv("MONGO_AUTH_SOURCE", "admin")

    if user and password:
        uri = (
            f"mongodb://{quote_plus(user)}:{quote_plus(password)}"
            f"@{host}:{port}/?authSource={auth_source}"
        )
    else:
        uri = f"mongodb://{host}:{port}/"

    return MongoClient(uri, serverSelectionTimeoutMS=5000)


def get_db(db_name: str | None = None) -> Database:
    client = get_client()
    return client[db_name or os.getenv("MONGO_DB", "nexus")]


if __name__ == "__main__":
    db = get_db()
    print(f"connected to db: {db.name!r}")
    print("collections:", db.list_collection_names())
