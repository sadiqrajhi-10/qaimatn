from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def now_utc():
    return datetime.now(timezone.utc)


class ShoppingItem(db.Model):
    __tablename__ = "shopping_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False, default="عام")
    done = db.Column(db.Boolean, nullable=False, default=False)
    added_by = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)


class WishlistItem(db.Model):
    __tablename__ = "wishlist_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    priority = db.Column(db.String(10), nullable=False, default="متوسطة")  # عالية / متوسطة / منخفضة
    price_estimate = db.Column(db.Float, nullable=True)
    done = db.Column(db.Boolean, nullable=False, default=False)
    added_by = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)


class Meal(db.Model):
    __tablename__ = "meals"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    meal_type = db.Column(db.String(10), nullable=False, default="عشاء")  # غداء / عشاء
    ingredients = db.Column(db.String(300), nullable=True)
    source = db.Column(db.String(10), nullable=False, default="يدوي")  # يدوي / AI
    added_by = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)
