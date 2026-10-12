import os
import secrets
from functools import wraps

import pymysql
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.exceptions import HTTPException

from db import get_conn
from security import hash_password, verify_password

load_dotenv()

app = Flask(__name__)
# The session secret lives in .env (never in the code)
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)


# ---------- helpers ----------

def login_required(view):
    """R3: a visitor who is not logged in is sent to the login page."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def check_title(title):
    """Server-side title rules (same messages as the browser)."""
    if not title:
        return "Title is required"
    if len(title) > 200:
        return "Title is too long (200 characters at most)"
    return None


def run_write(sql, params):
    """Run one INSERT/UPDATE/DELETE with parameters and commit."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def render_todos(errors=None, new_title="", edit_id=None, edit_title=""):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT todo_id, title, is_done, created_at FROM todos "
                "WHERE user_id = %s ORDER BY todo_id DESC",
                (session["user_id"],),
            )
            todos = cur.fetchall()
    finally:
        conn.close()
    return render_template(
        "todos.html", name=session["name"], todos=todos, errors=errors or [],
        new_title=new_title, edit_id=edit_id, edit_title=edit_title,
    )


# ---------- authentication ----------

@app.get("/")
def home():
    return redirect(url_for("todos" if "user_id" in session else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", errors=[], name="", email="")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    errors = []
    if not name:
        errors.append("Name is required")
    elif len(name) > 100:
        errors.append("Name is too long (100 characters at most)")
    if not email:
        errors.append("Email is required")
    elif len(email) > 255:
        errors.append("Email is too long (255 characters at most)")
    if not password:
        errors.append("Password is required")
    if not confirm:
        errors.append("Confirm password is required")
    if password and confirm and password != confirm:
        errors.append("Passwords do not match")

    if errors:  # R8: show the form again, do not touch the database
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
    except pymysql.err.IntegrityError as e:
        conn.rollback()
        if e.args[0] == 1062:  # duplicate entry on UNIQUE(email)
            return render_template(
                "register.html", errors=["Email Already Exists"], name=name, email=email
            )
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    session["user_id"] = user_id
    session["name"] = name
    return redirect(url_for("todos"))  # R1: logged in, sees the list


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", errors=[], email="")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    errors = []
    if not email:
        errors.append("Email is required")
    if not password:
        errors.append("Password is required")
    if errors:
        return render_template("login.html", errors=errors, email=email)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, name, password_hash FROM users WHERE email = %s",
                (email,),
            )
            user = cur.fetchone()
    finally:
        conn.close()

    # R2: unknown e-mail and wrong password give the very same message
    if user and verify_password(password, user["password_hash"]):
        session["user_id"] = user["user_id"]
        session["name"] = user["name"]
        return redirect(url_for("todos"))

    return render_template("login.html", errors=["Invalid email or password"], email=email)


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- to-do list (user_id always comes from the session) ----------

@app.get("/welcome")
def welcome():
    return redirect(url_for("todos"))


@app.get("/todos")
@login_required
def todos():
    return render_todos()


@app.post("/todos/add")
@login_required
def add_todo():
    title = request.form.get("title", "").strip()
    error = check_title(title)
    if error:
        return render_todos(errors=[error], new_title=title)
    run_write(
        "INSERT INTO todos (user_id, title) VALUES (%s, %s)",
        (session["user_id"], title),
    )
    return redirect(url_for("todos"))


@app.post("/todos/<int:todo_id>/edit")
@login_required
def edit_todo(todo_id):
    title = request.form.get("title", "").strip()
    error = check_title(title)
    if error:
        return render_todos(errors=[error], edit_id=todo_id, edit_title=title)
    run_write(
        "UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s",
        (title, todo_id, session["user_id"]),
    )
    return redirect(url_for("todos"))


@app.post("/todos/<int:todo_id>/toggle")
@login_required
def toggle_todo(todo_id):
    is_done = request.form.get("is_done")
    if is_done in ("0", "1"):
        run_write(
            "UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s",
            (int(is_done), todo_id, session["user_id"]),
        )
    return redirect(url_for("todos"))


@app.post("/todos/<int:todo_id>/delete")
@login_required
def delete_todo(todo_id):
    run_write(
        "DELETE FROM todos WHERE todo_id = %s AND user_id = %s",
        (todo_id, session["user_id"]),
    )
    return redirect(url_for("todos"))


# ---------- friendly error pages (no stack traces for the user) ----------

@app.errorhandler(Exception)
def handle_error(e):
    if isinstance(e, HTTPException):
        code = e.code or 500
    else:
        code = 500
        app.logger.exception(e)  # details go to the terminal only
    messages = {
        404: "We could not find that page.",
        405: "That action is not allowed here.",
    }
    message = messages.get(code, "Something went wrong on our side. Please try again.")
    return render_template("error.html", code=code, message=message), code


if __name__ == "__main__":
    app.run(debug=False)
