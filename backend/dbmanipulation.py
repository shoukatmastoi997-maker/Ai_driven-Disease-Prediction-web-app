import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "predictions.db"

con = sqlite3.connect(DB_PATH)
if con:
    print("Database Connected")
cur = con.cursor()
cur.execute("DELETE FROM PREDICTIONS WHERE Id = ?", (5,))
con.commit()
print("Record Deleted")
cur.execute(
    """
    SELECT pr.Id, pt.Name, pr.predicted_disease, pr.risk_level
    FROM PREDICTIONS pr
    JOIN PATIENT pt ON pr.patient_id = pt.patient_id
    ORDER BY pr.Id
    """
)
data = cur.fetchall()
for rec in data:
    print(rec)
con.close()
