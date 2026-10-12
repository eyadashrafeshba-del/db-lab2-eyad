import re
from flask import Flask, render_template, request, redirect, url_for, session
from db import get_conn
from security import hash_password, verify_password

app = Flask(__name__)
app.secret_key = "change-this-in-production"

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.get("/")
def home():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", errors=[], name="", email="")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    errors = []
    if not name: errors.append("Name is required")
    if not email: errors.append("Email is required")
    elif not EMAIL_PATTERN.match(email): errors.append("Email is not valid")
    if not password: errors.append("Password is required")
    if not confirm: errors.append("Confirm password is required")
    if password and confirm and password != confirm:
        errors.append("Passwords do not match")

    if errors:
        return render_template("register.html", errors=errors, name=name, email=email)

    pw_hash = hash_password(password)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                (email, name, pw_hash),
            )
            user_id = cur.lastrowid
        conn.commit()
    except Exception as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            errors.append("Email Already Exists")
            return render_template("register.html", errors=errors, name=name, email=email)
        raise
    finally:
        conn.close()

    session["user_id"] = user_id
    session["name"] = name
    return redirect(url_for("todos"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", errors=[], email="")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    errors = []
    if not email: errors.append("Email is required")
    elif not EMAIL_PATTERN.match(email): errors.append("Email is not valid")
    if not password: errors.append("Password is required")

    if errors:
        return render_template("login.html", errors=errors, email=email)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, name, password_hash FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
    finally:
        conn.close()

    if user and verify_password(password, user["password_hash"]):
        session["user_id"] = user["user_id"]
        session["name"] = user["name"]
        return redirect(url_for("todos"))

    errors.append("Invalid email or password")
    return render_template("login.html", errors=errors, email=email)


@app.get("/todos")
@login_required
def todos():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT todo_id, title, is_done FROM todos WHERE user_id = %s ORDER BY todo_id DESC",
                (session["user_id"],),
            )
            items = cur.fetchall()
    finally:
        conn.close()
    return render_template("todos.html", name=session["name"], items=items, errors=[])


@app.post("/todos/add")
@login_required
def todos_add():
    title = request.form.get("title", "").strip()
    if not title:
        return redirect(url_for("todos"))
    if len(title) > 200:
        title = title[:200]

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO todos (user_id, title) VALUES (%s, %s)",
                (session["user_id"], title),
            )
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for("todos"))


@app.post("/todos/edit/<int:todo_id>")
@login_required
def todos_edit(todo_id):
    title = request.form.get("title", "").strip()
    if not title:
        return redirect(url_for("todos"))
    if len(title) > 200:
        title = title[:200]

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s",
                (title, todo_id, session["user_id"]),
            )
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for("todos"))


@app.post("/todos/toggle/<int:todo_id>")
@login_required
def todos_toggle(todo_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE todos SET is_done = 1 - is_done WHERE todo_id = %s AND user_id = %s",
                (todo_id, session["user_id"]),
            )
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for("todos"))


@app.post("/todos/delete/<int:todo_id>")
@login_required
def todos_delete(todo_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM todos WHERE todo_id = %s AND user_id = %s",
                (todo_id, session["user_id"]),
            )
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for("todos"))


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)