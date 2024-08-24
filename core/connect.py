# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import os
import psycopg
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class PostgresConnection:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = psycopg.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
            )
            self.cursor = self.conn.cursor()
            print("PostgreSQLに接続しました。")
        except Exception as e:
            print(f"接続エラー: {e}")

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                return self.cursor.fetchall()
            else:
                self.conn.commit()
        except Exception as e:
            print(f"クエリエラー: {e}")

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

# インスタンスを作成して接続
pg_conn = PostgresConnection()
pg_conn.connect()
