from app.infrastructure.db.session import engine
from sqlalchemy import text

conn = engine.connect()
conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS pns_fit_score INTEGER"))
conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS pns_fit_data TEXT"))
conn.commit()
conn.close()
print("Columns added successfully")
