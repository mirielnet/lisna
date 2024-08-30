# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import os
import asyncpg
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class PostgresConnection:
    def __init__(self):
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
            )
            print("PostgreSQLに非同期で接続しました。")
        except Exception as e:
            print(f"接続エラー: {e}")
            self.pool = None

    async def execute_query(self, query, params=None):
        if not self.pool:
            raise Exception("接続が確立されていません。")

        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    if query.strip().upper().startswith("SELECT"):
                        result = await connection.fetch(query, *params) if params else await connection.fetch(query)
                        return result
                    else:
                        await connection.execute(query, *params) if params else await connection.execute(query)
        except Exception as e:
            print(f"クエリエラー: {e}")
            return None

    async def close(self):
        if self.pool:
            await self.pool.close()
            print("PostgreSQL接続を閉じました。")

# グローバルインスタンスを作成
db = PostgresConnection()

# 非同期で接続を確立
await db.connect()
