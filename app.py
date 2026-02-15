import os
import sqlite3
from flask import Flask, render_template, request, redirect, session
from datetime import timedelta

# Set up the app with Flask function and secret key, and also specify the session lifetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "DIGINOTES_12345")
app.permanent_session_lifetime = timedelta(days=12)

# Database path — use /tmp on Vercel (serverless writable directory)
DB_PATH = "/tmp/diginotes.db" if os.environ.get("VERCEL") else "diginotes.db"


def get_db():
    """Get a database connection, creating tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            note TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


# Define a home route (/) and check whether user's username is in session and if it is redirect to
# dashboard or else redirect to the home page

@app.route("/")
def main():
    if "username" in session:
        return redirect("/dashboard")
    return render_template("main.html")


# Define an account route where the user can sign in

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "GET":
        return render_template("account.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return render_template("account.html", message1="Missing username")
        elif not password:
            return render_template("account.html", message2="Missing password")

        session.permanent = True
        session["username"] = username

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

    return redirect("/")


# Define a dashboard route

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")
    else:
        return render_template("dashboard.html", username=session["username"])


# Specify a sign out route

@app.route("/sign_out")
def sign_out():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (session.get("username", ""),))
    conn.commit()
    conn.close()
    session.clear()
    return redirect("/")


# Define a landing route which is for the home icon on the dashboard

@app.route("/landing")
def landing():
    return render_template("main.html")


# Now define a route which will enable users to create todos

@app.route("/todo", methods=["GET", "POST"])
def todo():
    if request.method == "GET":
        return render_template("todo.html")
    else:
        title = request.form.get("title")
        note = request.form.get("text")

        if not title:
            return render_template("todo.html", message1="Hey, what will you call your to-do?")
        elif not note:
            return render_template("todo.html", message2="What task do you want to finish? Not none, right?")
        else:
            conn = get_db()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO notes (title, note) VALUES (?, ?)", (title, note))
            except sqlite3.IntegrityError:
                pass
            conn.commit()
            conn.close()

    return redirect("/todos")


# Define a todos route

@app.route("/todos")
def todos():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes;")
    rows = cursor.fetchall()
    conn.close()
    return render_template("todos.html", todos=rows)


# Define a delete route for deleting a todo when a user wants to

@app.route("/delete", methods=["POST"])
def delete():
    delete_id = request.form.get("final_delete")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (delete_id,))
    conn.commit()
    conn.close()
    return redirect("/todos")


# Define an update route, which will update the note at user's will

@app.route("/update", methods=["GET", "POST"])
def update():
    if request.method == "GET":
        update_id = request.args.get("update")
        session["note_id"] = update_id
        return render_template("update.html")
    else:
        updatedTitle = request.form.get("updated_title")
        updatedText = request.form.get("updated_text")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE notes SET title = ?, note = ? WHERE id = ?",
                        (updatedTitle, updatedText, session["note_id"]))
        conn.commit()
        conn.close()
    return redirect('/todos')
