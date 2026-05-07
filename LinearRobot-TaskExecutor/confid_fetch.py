# import requests


# url = "http://localhost:5173/api/config/"
# id="acceleration"
# res = requests.get(url+id)
# acceleration=res.json()['value']
# print(place_positions)

import sqlite3

conn = sqlite3.connect("task.db")

# Cursor lets you execute SQL
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER
)
""")

cur.execute(
    "DELETE FROM users WHERE name=?",
    ("Harish",)
)

conn.commit()