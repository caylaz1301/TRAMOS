from sqlalchemy import create_engine, text
import os

DATABASE_URL = "postgresql://postgres:postgres@localhost:5434/tramos_db"
engine = create_engine(DATABASE_URL)
with engine.connect() as connection:
    result = connection.execute(text("SELECT email, otp_code, is_verified FROM dashboard_users ORDER BY created_at DESC LIMIT 5"))
    for row in result:
        print(row)
