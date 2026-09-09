from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def now_utc():
    return datetime.now(timezone.utc)


class ShoppingItem(db.Model):
    __tablename__ = "shopping_items"

    id = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False, default="XCATX")
    note = db.Column(db.String(300), nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)
    done = db.Column(db.Boolean, nullable=False, default=False)
    done_at = db.Column(db.DateTime(timezone=True), nullable=True)
    added_by = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)


class SharedNote(db.Model):
    __tablename__ = "shared_note"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False, default="")
    updated_by = db.Column(db.String(30), nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class PushSubscription(db.Model):
    __tablename__ = "push_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(30), nullable=False)
    endpoint = db.Column(db.String(500), nullable=False, unique=True)
    p256dh = db.Column(db.String(200), nullable=False)
    auth = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)


class WishlistItem(db.Model):
    __tablename__ = "wishlist_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    priority = db.Column(db.String(10), nullable=False, default="XPRIX")
    price_estimate = db.Column(db.Float, nullable=True)
    done = db.Column(db.Boolean, nullable=False, default=False)
    done_at = db.Column(db.DateTime(timezone=True), nullable=True)
    bought_by = db.Column(db.String(30), nullable=True)
    added_by = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)


class MealProposal(db.Model):
    __tablename__ = "meal_proposal"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    meal_type = db.Column(db.String(10), nullable=False, default="XMEALX")
    proposed_by = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="XSTATUSX")
    response_note = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)
    responded_at = db.Column(db.DateTime(timezone=True), nullable=True)
