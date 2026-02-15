import os
from flask import Flask, render_template, request, redirect, session
from datetime import timedelta
from supabase import create_client, Client

# Set up the app with Flask function and secret key, and also specify the session lifetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "DIGINOTES_12345")
app.permanent_session_lifetime = timedelta(days=12)

# Supabase connection
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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

        # Insert user into Supabase
        supabase.table("users").insert({
            "username": username,
            "password": password
        }).execute()

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
    username = session.get("username", "")
    if username:
        supabase.table("users").delete().eq("username", username).execute()
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
            # Check if title already exists
            existing = supabase.table("notes").select("id").eq("title", title).execute()
            if not existing.data:
                supabase.table("notes").insert({
                    "title": title,
                    "note": note
                }).execute()

    return redirect("/todos")


# Define a todos route

@app.route("/todos")
def todos():
    result = supabase.table("notes").select("*").order("id").execute()
    # Convert Supabase rows (dicts) to tuples (id, title, note) for template compatibility
    rows = [(row["id"], row["title"], row["note"]) for row in result.data]
    return render_template("todos.html", todos=rows)


# Define a delete route for deleting a todo when a user wants to

@app.route("/delete", methods=["POST"])
def delete():
    delete_id = request.form.get("final_delete")
    if delete_id:
        supabase.table("notes").delete().eq("id", int(delete_id)).execute()
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

        note_id = session.get("note_id")
        if note_id:
            supabase.table("notes").update({
                "title": updatedTitle,
                "note": updatedText
            }).eq("id", int(note_id)).execute()

    return redirect('/todos')
