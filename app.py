import os, requests
from flask import Flask, request, redirect, session, flash, render_template
from jinja2 import DictLoader
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("FH_SECRET", "change-me")
URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/") + "/rest/v1"
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
KEY = KEY.strip()
H = {"apikey": KEY, "Content-Type": "application/json"}
if KEY.startswith("eyJ"):  # old-style JWT service_role key
    H["Authorization"] = "Bearer " + KEY

SERVICES = [
    ("niche", "Niche Boost: 10M Views + 1M Followers", "Instagram / Twitter / Facebook", 50),
    ("facebook", "Facebook Plan", "Followers, likes & reach", 500),
    ("instagram", "Instagram Plan", "Followers, likes & views", 500),
    ("twitter", "Twitter Plan", "Followers, likes & views", 500),
    ("youtube", "YouTube Plan", "Subscribers, views & watch time", 500),
]

def sb(method, path, headers=None, **kw):
    return requests.request(method, URL + path, headers={**H, **(headers or {})}, timeout=15, **kw)

def me():
    if "uid" not in session: return None
    r = sb("GET", "/users", params={"id": f"eq.{int(session['uid'])}", "select": "id,username,balance"})
    d = r.json() if r.ok else []
    return d[0] if d else None

@app.route("/")
def home():
    return render_template("home.html", services=SERVICES, user=me())

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        u, p = request.form["username"].strip(), request.form["password"]
        if len(u) < 3 or len(p) < 4:
            flash("Username min 3, password min 4 character.")
        else:
            r = sb("POST", "/users", headers={"Prefer": "return=representation"},
                   json={"username": u, "pw": generate_password_hash(p)})
            if r.status_code == 409: flash("Ei username already ache.")
            elif r.ok:
                session["uid"] = r.json()[0]["id"]; return redirect("/dashboard")
            else: flash(f"Error {r.status_code}: {r.text[:200]}")
    return render_template("auth.html", title="Sign Up", user=None)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        r = sb("GET", "/users", params={"username": "eq." + request.form["username"].strip(), "select": "*"})
        d = r.json() if r.ok else []
        if d and check_password_hash(d[0]["pw"], request.form["password"]):
            session["uid"] = d[0]["id"]; return redirect("/dashboard")
        flash("Username ba password vul.")
    return render_template("auth.html", title="Login", user=None)

@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

@app.route("/dashboard")
def dashboard():
    u = me()
    if not u: return redirect("/login")
    o = sb("GET", "/orders", params={"user_id": f"eq.{u['id']}", "order": "id.desc", "limit": 20}).json()
    f = sb("GET", "/funds", params={"user_id": f"eq.{u['id']}", "order": "id.desc", "limit": 10}).json()
    return render_template("dashboard.html", user=u, services=SERVICES, orders=o, funds=f)

@app.route("/addfund", methods=["POST"])
def addfund():
    u = me()
    if not u: return redirect("/login")
    r = sb("POST", "/rpc/redeem_code", json={"p_code": request.form["code"].strip(), "p_user": u["id"]})
    amt = r.json() if r.ok else 0
    flash(f"{amt} tk add hoyeche!" if isinstance(amt, int) and amt > 0 else "Code vul ba already use kora hoyeche.")
    return redirect("/dashboard")

@app.route("/buy", methods=["POST"])
def buy():
    u = me()
    if not u: return redirect("/login")
    s = next((x for x in SERVICES if x[0] == request.form["service"]), None)
    link = request.form["link"].strip()
    if not s or not link: flash("Link din.")
    else:
        r = sb("POST", "/rpc/buy_plan", json={"p_user": u["id"], "p_service": s[1], "p_link": link, "p_price": s[3]})
        flash("Order successful!" if r.ok and r.json() is True else "Balance kom! Age Add Fund korun.")
    return redirect("/dashboard")

T = {}
T["base.html"] = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FollowerHouse</title><style>
:root{--g:#22c55e;--bg:#0b0f0c;--card:#121a14;--t:#e8f5ec;--m:#8aa593}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--t);font-family:system-ui,sans-serif}
header{display:flex;align-items:center;justify-content:space-between;padding:14px 5%;border-bottom:1px solid #1e2b22}
.brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:22px;color:var(--t);text-decoration:none}
.brand img{width:42px;height:42px;border-radius:10px}nav a{color:var(--m);margin-left:16px;text-decoration:none}
.wrap{max-width:1000px;margin:auto;padding:24px 5%}.hero{text-align:center;padding:40px 0}
.hero img{width:110px;border-radius:24px}.hero h1{font-size:40px;margin:14px 0 6px}.hero p{color:var(--m)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.card{background:var(--card);border:1px solid #1e2b22;border-radius:16px;padding:20px}
.price{color:var(--g);font-size:28px;font-weight:800}.muted{color:var(--m);font-size:14px}
.btn,button{background:var(--g);color:#04210e;border:0;padding:10px 18px;border-radius:10px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-block}
input{width:100%;padding:11px;margin:6px 0;background:#0b0f0c;border:1px solid #28402f;border-radius:10px;color:var(--t)}
.flash{background:#14301d;border:1px solid var(--g);padding:10px 14px;border-radius:10px;margin-bottom:14px}
table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #1e2b22;text-align:left;font-size:14px}
.bal{font-size:34px;color:var(--g);font-weight:800}
</style></head><body>
<header><a class="brand" href="/"><img src="/logo.png" alt="FH">FollowerHouse</a>
<nav>{% if user %}<a href="/dashboard">Dashboard</a><a href="/logout">Logout</a>{% else %}<a href="/login">Login</a><a href="/signup">Sign Up</a>{% endif %}</nav></header>
<div class="wrap">{% with m=get_flashed_messages() %}{% for x in m %}<div class="flash">{{x}}</div>{% endfor %}{% endwith %}
{% block c %}{% endblock %}</div></body></html>"""
T["home.html"] = """{% extends 'base.html' %}{% block c %}
<div class="hero"><img src="/logo.png" alt="FH"><h1>FollowerHouse</h1>
<p>Boost your social media. Fast, cheap and simple.</p><br><a class="btn" href="/signup">Get Started</a></div>
<div class="grid">{% for k,n,d,p in services %}<div class="card"><h3>{{n}}</h3><p class="muted">{{d}}</p><div class="price">{{p}} tk</div></div>{% endfor %}</div>
{% endblock %}"""
T["auth.html"] = """{% extends 'base.html' %}{% block c %}<div class="card" style="max-width:380px;margin:30px auto"><h2>{{title}}</h2>
<form method="post"><input name="username" placeholder="Username" required><input name="password" type="password" placeholder="Password" required>
<button>{{title}}</button></form></div>{% endblock %}"""
T["dashboard.html"] = """{% extends 'base.html' %}{% block c %}
<div class="grid"><div class="card"><div class="muted">Balance</div><div class="bal">{{user.balance}} tk</div><p class="muted">Hi, {{user.username}}</p></div>
<div class="card"><h3>Add Fund</h3><p class="muted">Owner theke code niye ekhane din.</p>
<form method="post" action="/addfund"><input name="code" placeholder="Enter code (e.g. FH-AB12CD)" required><button>Add Fund</button></form></div></div>
<h2>Buy a Plan</h2><div class="grid">{% for k,n,d,p in services %}<div class="card"><h3>{{n}}</h3><p class="muted">{{d}}</p><div class="price">{{p}} tk</div>
<form method="post" action="/buy"><input type="hidden" name="service" value="{{k}}"><input name="link" placeholder="Your profile / post link" required><button>Buy</button></form></div>{% endfor %}</div>
<h2>Orders</h2><div class="card"><table><tr><th>Service</th><th>Link</th><th>Price</th><th>Date</th></tr>
{% for o in orders %}<tr><td>{{o.service}}</td><td>{{o.link}}</td><td>{{o.price}} tk</td><td>{{o.created_at}}</td></tr>{% else %}<tr><td colspan=4 class="muted">No orders yet</td></tr>{% endfor %}</table></div>
<h2>Fund History</h2><div class="card"><table>{% for f in funds %}<tr><td>+{{f.amount}} tk</td><td>{{f.created_at}}</td></tr>{% else %}<tr><td class="muted">No funds yet</td></tr>{% endfor %}</table></div>
{% endblock %}"""
app.jinja_loader = DictLoader(T)
