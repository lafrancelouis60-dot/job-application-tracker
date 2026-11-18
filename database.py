import os

import mysql.connector
from dotenv import load_dotenv
from flask import g

load_dotenv()


def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "job_tracker_user"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "job_tracker"),
        )
    return g.db


def close_db(error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def query(sql, params=(), one=False):
    with get_db().cursor(dictionary=True) as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone() if one else cursor.fetchall()


def execute(sql, params=()):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            new_id = cursor.lastrowid
        connection.commit()
        return new_id
    except mysql.connector.Error:
        connection.rollback()
        raise