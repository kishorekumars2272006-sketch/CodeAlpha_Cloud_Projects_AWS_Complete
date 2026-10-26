import os
import hashlib
import secrets
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP

from flask import Flask, request, redirect, url_for, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
database_url = os.environ.get("DATABASE_URL", "sqlite:///codealpha.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Task 1: Data Redundancy Removal System
class DataRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_key = db.Column(db.String(120), nullable=False, unique=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# Task 3: Cloud-Based Bus Pass System
class BusPass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_code = db.Column(db.String(20), nullable=False, unique=True, index=True)
    passenger_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    route = db.Column(db.String(100), nullable=False)
    pass_type = db.Column(db.String(20), nullable=False)
    travel_date = db.Column(db.Date, nullable=False)
    price_paise = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="CONFIRMED")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# Prices are set on the server, never trusted from a form field.
ROUTES = {
    "Chennai Central - Tambaram": {"single": 2500, "daily": 5000, "monthly": 90000},
    "Chennai Central - Avadi": {"single": 3000, "daily": 6000, "monthly": 110000},
    "Guindy - Sholinganallur": {"single": 3500, "daily": 7000, "monthly": 125000},
}
PASS_TYPES = {
    "single": "Single trip",
    "daily": "Daily pass",
    "monthly": "Monthly pass",
}


def normalize_record(name, email, category):
    """Normalize harmless formatting differences before hashing."""
    return {
        "name": " ".join(name.strip().split()).casefold(),
        "email": email.strip().casefold(),
        "category": " ".join(category.strip().split()).casefold(),
    }


def record_fingerprint(name, email, category):
    normalized = normalize_record(name, email, category)
    canonical = "|".join(normalized[k] for k in ("name", "email", "category"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def money(paise):
    return f"₹{paise / 100:,.2f}"


PAGE = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CodeAlpha Cloud Projects</title>
<style>
:root{font-family:Arial,sans-serif;color:#172033;background:#f4f7fb}
body{margin:0}header{background:#12213d;color:white;padding:24px max(20px,calc((100% - 1050px)/2))}
main{max-width:1050px;margin:24px auto;padding:0 16px}
nav a{color:#fff;margin-right:18px;text-decoration:none;font-weight:bold}
h1{margin:0 0 10px}h2{margin-top:0}.sub{color:#d8e2f2}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:18px}
.card{background:white;border-radius:14px;padding:22px;box-shadow:0 3px 15px #13264a12;margin-bottom:18px}
input,select{box-sizing:border-box;width:100%;padding:11px;border:1px solid #c8d2e1;border-radius:8px;margin:5px 0 13px}
button,.btn{display:inline-block;background:#145de0;color:white;padding:11px 15px;border:0;border-radius:8px;text-decoration:none;cursor:pointer}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:10px;border-bottom:1px solid #e5eaf1}
th{background:#f4f7fb}.flash{padding:12px;border-radius:8px;background:#e7f7ed;margin:12px 0}.error{background:#fff0ef}
.small{color:#64748b;font-size:13px}.price{font-size:22px;font-weight:bold;color:#145de0}
@media(max-width:600px){table{display:block;overflow-x:auto}}
</style>
</head>
<body>
<header><h1>CodeAlpha Cloud Projects</h1><div class="sub">Task 1 · Data Redundancy Removal &nbsp; | &nbsp; Task 3 · Cloud-Based Bus Pass</div><p><nav><a href="/">Dashboard</a><a href="/redundancy">Task 1</a><a href="/bus-pass">Task 3</a></nav></p></header>
<main>
{% with messages = get_flashed_messages(with_categories=true) %}
{% for category, message in messages %}<div class="flash {{ 'error' if category == 'error' else '' }}">{{ message }}</div>{% endfor %}
{% endwith %}
{{ body|safe }}
<footer class="small">Student demonstration project. Use fictional data only. For real public deployment, add authentication, rate limiting, privacy controls and operational monitoring.</footer>
</main></body></html>
"""


def page(body, **context):
    return render_template_string(PAGE, body=render_template_string(body, **context))


@app.route("/")
def index():
    record_count = DataRecord.query.count()
    pass_count = BusPass.query.count()
    return page("""
    <div class="grid">
      <section class="card"><h2>Task 1: Data Redundancy Removal</h2>
      <p>Validate fields, normalize harmless formatting differences, detect duplicates and store only unique records.</p>
      <p class="price">{{ record_count }} unique records</p><a class="btn" href="{{ url_for('redundancy') }}">Open Task 1</a></section>
      <section class="card"><h2>Task 3: Cloud-Based Bus Pass</h2>
      <p>Book a pass with server-side route pricing and a unique booking code.</p>
      <p class="price">{{ pass_count }} bookings</p><a class="btn" href="{{ url_for('bus_pass') }}">Open Task 3</a></section>
    </div>
    <section class="card"><h2>Project features</h2><ul><li>Database uniqueness constraints</li><li>Input validation and clear duplicate messages</li><li>Booking code for each pass</li><li>Server-calculated prices to prevent price tampering</li><li>SQLite locally; PostgreSQL supported for AWS deployment</li></ul></section>
    """, record_count=record_count, pass_count=pass_count)


@app.route("/redundancy", methods=["GET", "POST"])
def redundancy():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        category = request.form.get("category", "").strip()
        if not name or len(name) > 120 or not email or len(email) > 254 or "@" not in email or "." not in email.rsplit("@", 1)[-1] or not category or len(category) > 80:
            flash("Please enter a valid name, email address and category.", "error")
            return redirect(url_for("redundancy"))
        key = record_fingerprint(name, email, category)
        existing = DataRecord.query.filter_by(record_key=key).first()
        if existing:
            flash(f"Duplicate detected: this matches existing record #{existing.id}. Nothing was added.", "error")
            return redirect(url_for("redundancy"))
        try:
            record = DataRecord(record_key=key, name=" ".join(name.split()), email=email.lower(), category=" ".join(category.split()))
            db.session.add(record)
            db.session.commit()
            flash(f"Verified unique record added successfully (ID {record.id}).")
        except IntegrityError:
            db.session.rollback()
            flash("A matching record was added at the same time. Duplicate prevented.", "error")
        return redirect(url_for("redundancy"))
    records = DataRecord.query.order_by(DataRecord.id.desc()).limit(100).all()
    return page("""
    <section class="card"><h2>Task 1 — Add a verified record</h2>
    <p>Records are compared using normalized name + email + category. A matching fingerprint is treated as a duplicate. This simple rule is transparent but is not a universal definition of duplicate data.</p>
    <form method="post">
    <label>Name</label><input name="name" maxlength="120" required placeholder="Example: Priya Kumar">
    <label>Email</label><input name="email" type="email" maxlength="254" required placeholder="priya@example.com">
    <label>Category</label><input name="category" maxlength="80" required placeholder="Example: Student">
    <button type="submit">Validate and save</button></form></section>
    <section class="card"><h2>Stored records (latest 100)</h2>
    {% if records %}<table><tr><th>ID</th><th>Name</th><th>Email</th><th>Category</th><th>Created (UTC)</th></tr>
    {% for r in records %}<tr><td>{{r.id}}</td><td>{{r.name}}</td><td>{{r.email}}</td><td>{{r.category}}</td><td>{{r.created_at.strftime('%Y-%m-%d %H:%M')}}</td></tr>{% endfor %}</table>
    {% else %}<p>No records yet. Add your first record above.</p>{% endif %}</section>
    """, records=records)


@app.route("/bus-pass", methods=["GET", "POST"])
def bus_pass():
    if request.method == "POST":
        name = request.form.get("passenger_name", "").strip()
        email = request.form.get("email", "").strip()
        route = request.form.get("route", "")
        pass_type = request.form.get("pass_type", "")
        travel_date_raw = request.form.get("travel_date", "")
        if not name or len(name) > 120 or not email or len(email) > 254 or "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            flash("Enter a valid passenger name and email.", "error")
            return redirect(url_for("bus_pass"))
        if route not in ROUTES or pass_type not in PASS_TYPES:
            flash("Choose a valid route and pass type.", "error")
            return redirect(url_for("bus_pass"))
        try:
            travel_date = date.fromisoformat(travel_date_raw)
        except ValueError:
            flash("Choose a valid travel date.", "error")
            return redirect(url_for("bus_pass"))
        if travel_date < date.today():
            flash("Travel date cannot be in the past.", "error")
            return redirect(url_for("bus_pass"))
        price = ROUTES[route][pass_type]
        code = "CA-" + secrets.token_hex(4).upper()
        booking = BusPass(booking_code=code, passenger_name=" ".join(name.split()), email=email.lower(),
                          route=route, pass_type=pass_type, travel_date=travel_date, price_paise=price)
        try:
            db.session.add(booking)
            db.session.commit()
            flash(f"Booking confirmed! Your code is {code}. Price: {money(price)}.")
        except IntegrityError:
            db.session.rollback()
            flash("Booking could not be saved due to a code collision. Please submit again.", "error")
        return redirect(url_for("bus_pass"))
    bookings = BusPass.query.order_by(BusPass.id.desc()).limit(100).all()
    return page("""
    <section class="card"><h2>Task 3 — Book a bus pass</h2>
    <p>Pricing is calculated on the server. Any edited price sent from the browser is ignored.</p>
    <form method="post">
    <label>Passenger name</label><input name="passenger_name" maxlength="120" required>
    <label>Email</label><input name="email" type="email" maxlength="254" required>
    <label>Route</label><select name="route" required>{% for route in routes %}<option value="{{route}}">{{route}}</option>{% endfor %}</select>
    <label>Pass type</label><select name="pass_type" required>{% for key,label in pass_types.items() %}<option value="{{key}}">{{label}}</option>{% endfor %}</select>
    <label>Travel start date</label><input type="date" name="travel_date" min="{{today}}" value="{{today}}" required>
    <button type="submit">Book pass</button></form>
    <p class="small">Demo prices: single trip ₹25–₹35; daily pass ₹50–₹70; monthly pass ₹900–₹1,250 depending on route. These are sample prices, not real fares.</p></section>
    <section class="card"><h2>Recent bookings (latest 100)</h2>
    {% if bookings %}<table><tr><th>Code</th><th>Passenger</th><th>Route</th><th>Type</th><th>Date</th><th>Price</th><th>Status</th></tr>
    {% for b in bookings %}<tr><td>{{b.booking_code}}</td><td>{{b.passenger_name}}</td><td>{{b.route}}</td><td>{{pass_types[b.pass_type]}}</td><td>{{b.travel_date.isoformat()}}</td><td>{{money(b.price_paise)}}</td><td>{{b.status}}</td></tr>{% endfor %}</table>
    {% else %}<p>No bookings yet. Try a sample booking above.</p>{% endif %}</section>
    """, bookings=bookings, routes=ROUTES.keys(), pass_types=PASS_TYPES, today=date.today().isoformat(), money=money)


@app.get("/health")
def health():
    return {"status": "ok"}, 200


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
