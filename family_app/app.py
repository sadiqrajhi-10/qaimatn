import random
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash

from config import Config
from models import db, ShoppingItem, WishlistItem, Meal

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()


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
    return {"current_user": session.get("user")}


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
    items = ShoppingItem.query.order_by(ShoppingItem.done, ShoppingItem.created_at.desc()).all()
    return render_template("shopping.html", items=items)


@app.route("/shopping/add", methods=["POST"])
@user_required
def shopping_add():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip() or "عام"
    if name:
        db.session.add(ShoppingItem(name=name, category=category, added_by=session["user"]))
        db.session.commit()
    return redirect(url_for("shopping"))


@app.route("/shopping/toggle/<int:item_id>", methods=["POST"])
@user_required
def shopping_toggle(item_id):
    item = ShoppingItem.query.get_or_404(item_id)
    item.done = not item.done
    db.session.commit()
    return redirect(url_for("shopping"))


@app.route("/shopping/delete/<int:item_id>", methods=["POST"])
@user_required
def shopping_delete(item_id):
    item = ShoppingItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("shopping"))


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
