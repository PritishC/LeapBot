"""
Module to setup Database on a fresh installation.
"""

import sqlite3


def setup_db():
    connection = sqlite3.connect("irc.db")
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE last_seen
                      (nick TEXT PRIMARY KEY, time TEXT, last_msg TEXT)""")
    connection.close()


if __name__ == "__main__":
    setup_db()
