import sqlite3
con=sqlite3.connect("backend/predictions.db")
if(con):
    print("Database Connected")
cur=con.cursor()
cur.execute("Delete from predictions where id=5")
con.commit()
print("Record Deleted")
cur.execute("Select * from predictions")
data=cur.fetchall()
for rec in data:
   print(rec)
