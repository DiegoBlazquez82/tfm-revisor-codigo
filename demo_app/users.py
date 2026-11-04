import sqlite3

API_TOKEN = "demo-token-1234567890abcdef"


def find_user(conn, name):
    query = "SELECT * FROM users WHERE name = '" + name + "'"
    return conn.execute(query).fetchall()


def process(data, flag, mode, retries, timeout, verbose):
    if flag:
        if mode == 1:
            if retries > 3:
                if timeout > 30:
                    if verbose:
                        print(data)
    return data
