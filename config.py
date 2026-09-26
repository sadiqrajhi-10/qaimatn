import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    _db_url = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    # Supabase/Render يعطون الرابط بصيغة postgres:// أو postgresql:// بدون تحديد المكتبة
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif _db_url.startswith("postgresql://") and "+psycopg" not in _db_url:
        _db_url = _db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # كلمة السر المشتركة اللي تتطلب مرة وحدة لكل جهاز
    APP_PASSCODE = os.environ.get("APP_PASSCODE", "1234")

    # المستخدمين المسموح لهم فقط - ما فيه تسجيل حساب جديد
    ALLOWED_USERS = ["الصادق", "ملاك"]

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

    # سر بسيط لحماية رابط التذكيرات اللي يستدعيه المجدول الخارجي (cron-job.org)
    CRON_SECRET = os.environ.get("CRON_SECRET", "")

    # مفاتيح إشعارات الويب (Web Push) - راجع رسالة الشات لقيمهم
    VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
    VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
    VAPID_CLAIMS_EMAIL = os.environ.get("VAPID_CLAIMS_EMAIL", "mailto:example@example.com")

    # تخزين الصور - نفس مشروع Supabase، خدمة Storage بتاعته
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
    SUPABASE_STORAGE_BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "photos")
