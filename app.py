from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "tasks.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password))
            )
            conn.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("An account with this email already exists.", "error")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? ORDER BY due_date IS NULL, due_date, id DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return render_template("dashboard.html", tasks=tasks, name=session["user_name"])

@app.route("/tasks/add", methods=["POST"])
@login_required
def add_task():
    title = request.form["title"].strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("due_date", "")
    priority = request.form.get("priority", "Medium")

    if title:
        conn = get_db()
        conn.execute(
            """INSERT INTO tasks (user_id, title, description, due_date, priority)
               VALUES (?, ?, ?, ?, ?)""",
            (session["user_id"], title, description, due_date, priority)
        )
        conn.commit()
        conn.close()
        flash("Task added successfully.", "success")
    else:
        flash("Task title is required.", "error")

    return redirect(url_for("dashboard"))

@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    conn = get_db()
    task = conn.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"])
    ).fetchone()

    if not task:
        conn.close()
        flash("Task not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form.get("description", "").strip()
        due_date = request.form.get("due_date", "")
        priority = request.form.get("priority", "Medium")
        status = request.form.get("status", "Pending")

        conn.execute(
            """UPDATE tasks
               SET title = ?, description = ?, due_date = ?, priority = ?, status = ?
               WHERE id = ? AND user_id = ?""",
            (title, description, due_date, priority, status, task_id, session["user_id"])
        )
        conn.commit()
        conn.close()
        flash("Task updated successfully.", "success")
        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("edit_task.html", task=task)

@app.route("/tasks/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle_task(task_id):
    conn = get_db()
    task = conn.execute(
        "SELECT status FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"])
    ).fetchone()

    if task:
        new_status = "Completed" if task["status"] != "Completed" else "Pending"
        conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ? AND user_id = ?",
            (new_status, task_id, session["user_id"])
        )
        conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"])
    )
    conn.commit()
    conn.close()
    flash("Task deleted.", "success")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
