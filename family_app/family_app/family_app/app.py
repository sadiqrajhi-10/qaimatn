import random
import json as json_lib
from datetime import timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

from config import Config
from models import db, ShoppingItem, WishlistItem, Meal, SharedNote, PushSubscription, now_utc

try:
    from pywebpush import webpush, WebPushException
except ImportError:
    webpush = None
    WebPushException = Exception

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

# بعد ما يتحدد الغرض "تم شراؤه"، يفضل بان بشكل باهت لهالمدة قبل ما يختفي نهائيًا
FADE_HOURS = 6


def added_verb(user):
    return "ضافت" if user == "ملاك" else "ضاف"


def notify_other_user(current_user, title, body):
    """يبعت إشعار Web Push للطرف الثاني (مو اللي سوى الإضافة)."""
    if not webpush or not app.config.get("VAPID_PRIVATE_KEY"):
        return
    other_users = [u for u in app.config["ALLOWED_USERS"] if u != current_user]
    subs = PushSubscription.query.filter(PushSubscription.user.in_(other_users)).all()
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=json_lib.dumps({"title": title, "body": body}),
                vapid_private_key=app.config["VAPID_PRIVATE_KEY"],
                vapid_claims={"sub": app.config["VAPID_CLAIMS_EMAIL"]},
            )
        except WebPushException as e:
            if "410" in str(e) or "404" in str(e):
                db.session.delete(sub)
    db.session.commit()


# ---------- حماية الصفحات ----------

def passcode_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authed"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def user_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authed"):
            return redirect(url_for("login", next=request.path))
        if session.get("user") not in app.config["ALLOWED_USERS"]:
            return redirect(url_for("pick_user", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_current_user():
    return {"current_user": session.get("user"), "vapid_public_key": app.config.get("VAPID_PUBLIC_KEY", "")}


# ---------- الدخول ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        entered = request.form.get("passcode", "")
        if entered == app.config["APP_PASSCODE"]:
            session["authed"] = True
            return redirect(url_for("pick_user"))
        flash("كلمة السر غلط، حاول مرة ثانية")
    return render_template("login.html")


@app.route("/pick-user", methods=["GET", "POST"])
@passcode_required
def pick_user():
    if request.method == "POST":
        chosen = request.form.get("user")
        if chosen in app.config["ALLOWED_USERS"]:
            session["user"] = chosen
            return redirect(url_for("shopping"))
    return render_template("pick_user.html", users=app.config["ALLOWED_USERS"])


@app.route("/switch-user")
def switch_user():
    session.pop("user", None)
    return redirect(url_for("pick_user"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    return redirect(url_for("shopping"))


# ---------- قائمة النواقص ----------

@app.route("/shopping", methods=["GET"])
@user_required
def shopping():
    cutoff = now_utc() - timedelta(hours=FADE_HOURS)
    items = (
        ShoppingItem.query
        .filter(db.or_(ShoppingItem.done.is_(False), ShoppingItem.done_at > cutoff))
        .order_by(ShoppingItem.done, ShoppingItem.created_at.desc())
        .all()
    )
    category_rows = (
        db.session.query(ShoppingItem.category, db.func.min(ShoppingItem.created_at))
        .group_by(ShoppingItem.category)
        .order_by(db.func.min(ShoppingItem.created_at))
        .all()
    )
    categories = [row[0] for row in category_rows]
    shared_note = SharedNote.query.first()
    return render_template("shopping.html", items=items, categories=categories, shared_note=shared_note)


@app.route("/shopping/add", methods=["POST"])
@user_required
def shopping_add():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip() or "عام"
    note = request.form.get("note", "").strip() or None
    if name:
        db.session.add(ShoppingItem(name=name, category=category, note=note, added_by=session["user"]))
        db.session.commit()
        notify_other_user(session["user"], "قائمتنا", f'{session["user"]} {added_verb(session["user"])} "{name}" للنواقص')
    return redirect(url_for("shopping"))


@app.route("/shopping/toggle/<int:item_id>", methods=["POST"])
@user_required
def shopping_toggle(item_id):
    item = ShoppingItem.query.get_or_404(item_id)
    item.done = not item.done
    item.done_at = now_utc() if item.done else None
    db.session.commit()
    return redirect(url_for("shopping"))


@app.route("/shopping/delete/<int:item_id>", methods=["POST"])
@user_required
def shopping_delete(item_id):
    item = ShoppingItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("shopping"))


@app.route("/note/update", methods=["POST"])
@user_required
def note_update():
    content = request.form.get("content", "").strip()
    note = SharedNote.query.first()
    if not note:
        note = SharedNote()
        db.session.add(note)
    note.content = content
    note.updated_by = session["user"]
    db.session.commit()
    return redirect(url_for("shopping"))


@app.route("/push/subscribe", methods=["POST"])
@user_required
def push_subscribe():
    data = request.get_json(force=True, silent=True) or {}
    endpoint = data.get("endpoint")
    keys = data.get("keys", {})
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")
    if not endpoint or not p256dh or not auth:
        return jsonify({"ok": False}), 400
    existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if existing:
        existing.user = session["user"]
        existing.p256dh = p256dh
        existing.auth = auth
    else:
        db.session.add(PushSubscription(user=session["user"], endpoint=endpoint, p256dh=p256dh, auth=auth))
    db.session.commit()
    return jsonify({"ok": True})


# ---------- قائمة الأمنيات ----------

@app.route("/wishlist", methods=["GET"])
@user_required
def wishlist():
    order = {"عالية": 0, "متوسطة": 1, "منخفضة": 2}
    items = WishlistItem.query.order_by(WishlistItem.done).all()
    items.sort(key=lambda i: order.get(i.priority, 1))
    return render_template("wishlist.html", items=items)


@app.route("/wishlist/add", methods=["POST"])
@user_required
def wishlist_add():
    name = request.form.get("name", "").strip()
    priority = request.form.get("priority", "متوسطة")
    price_raw = request.form.get("price_estimate", "").strip()
    price = float(price_raw) if price_raw else None
    if name:
        db.session.add(WishlistItem(name=name, priority=priority, price_estimate=price, added_by=session["user"]))
        db.session.commit()
        notify_other_user(session["user"], "قائمتنا", f'{session["user"]} {added_verb(session["user"])} "{name}" للأمنيات')
    return redirect(url_for("wishlist"))


@app.route("/wishlist/toggle/<int:item_id>", methods=["POST"])
@user_required
def wishlist_toggle(item_id):
    item = WishlistItem.query.get_or_404(item_id)
    item.done = not item.done
    db.session.commit()
    return redirect(url_for("wishlist"))


@app.route("/wishlist/delete/<int:item_id>", methods=["POST"])
@user_required
def wishlist_delete(item_id):
    item = WishlistItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("wishlist"))


# ---------- الأكل ----------

@app.route("/meals", methods=["GET"])
@user_required
def meals():
    saved_meals = Meal.query.filter_by(source="يدوي").order_by(Meal.created_at.desc()).all()
    suggestion = session.pop("last_suggestion", None)
    return render_template("meals.html", saved_meals=saved_meals, suggestion=suggestion)


@app.route("/meals/add", methods=["POST"])
@user_required
def meals_add():
    name = request.form.get("name", "").strip()
    meal_type = request.form.get("meal_type", "عشاء")
    ingredients = request.form.get("ingredients", "").strip()
    if name:
        db.session.add(Meal(name=name, meal_type=meal_type, ingredients=ingredients,
                             source="يدوي", added_by=session["user"]))
        db.session.commit()
        notify_other_user(session["user"], "قائمتنا", f'{session["user"]} {added_verb(session["user"])} وصفة "{name}"')
    return redirect(url_for("meals"))


@app.route("/meals/suggest", methods=["POST"])
@user_required
def meals_suggest():
    meal_type = request.form.get("meal_type", "عشاء")
    available = request.form.get("available", "").strip()

    ai_text = get_ai_suggestion(available, meal_type) if available else None

    if ai_text:
        session["last_suggestion"] = {"text": ai_text, "source": "AI"}
    else:
        candidates = Meal.query.filter_by(source="يدوي", meal_type=meal_type).all()
        if candidates:
            pick = random.choice(candidates)
            session["last_suggestion"] = {
                "text": f"{pick.name}" + (f" ({pick.ingredients})" if pick.ingredients else ""),
                "source": "من قائمتكم",
            }
        else:
            session["last_suggestion"] = {
                "text": "ما فيه اقتراحات بعد - ضيفوا وصفة أو اكتبوا المكونات المتوفرة",
                "source": "تنبيه",
            }
    return redirect(url_for("meals"))


def get_ai_suggestion(available_ingredients: str, meal_type: str):
    """يبعت طلب لـ Gemini API. يرجع None لو ما فيه مفتاح أو صار خطأ، وقتها نرجع لقائمتنا اليدوية."""
    api_key = app.config.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            f"اقترح فكرة {meal_type} بسيطة وسريعة باستخدام هذي المكونات المتوفرة: "
            f"{available_ingredients}. جاوب بجملة أو جملتين بس بالعربي."
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return None


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
