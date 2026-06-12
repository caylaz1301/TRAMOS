import sys
sys.path.insert(0, "/app")
from app.database_models import DatabaseManager
from app.config import settings

db = DatabaseManager(settings.DATABASE_URL)
try:
    res = db.execute_query("SELECT count(*) FROM knowledge_base_chunks")
    print("KB chunks:", res[0][0] if res else 0)
except Exception as e:
    print("Error:", e)
    try:
        res2 = db.execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", ("public",))
        print("Tables:", [r[0] for r in res2])
    except Exception as e2:
        print("Tables error:", e2)
