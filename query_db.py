"""Helper kecil untuk mengecek OTP user dashboard dari database lokal."""

from sqlalchemy import create_engine, text

from app.config import settings


engine = create_engine(settings.DATABASE_URL)
with engine.connect() as connection:
    result = connection.execute(text("SELECT email, otp_code, is_verified FROM dashboard_users ORDER BY created_at DESC LIMIT 5"))
    for row in result:
        print(row)
