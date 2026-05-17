import sqlite3
conn = sqlite3.connect('youshop.db')
conn.execute("ALTER TABLE products ADD COLUMN unit TEXT DEFAULT 'piece';")
conn.commit()
conn.close()
print("done")