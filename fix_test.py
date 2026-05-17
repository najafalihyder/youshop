import sqlite3
conn = sqlite3.connect('youshop.db')
conn.execute("ALTER TABLE users ADD COLUMN phone TEXT;")
conn.commit()
conn.close()
print("done")