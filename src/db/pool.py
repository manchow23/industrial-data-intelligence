import os
from psycopg2.pool import SimpleConnectionPool

from src.settings import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
)

pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=POSTGRES_HOST,
    port=int(POSTGRES_PORT),
    database=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
)

def get_pool():
    return pool