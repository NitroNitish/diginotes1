import os
from flask import Flask, render_template, request, redirect, session
from datetime import timedelta

# Set up the app with Flask function and secret key, and also specify the session lifetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "DIGINOTES_12345")
app.permanent_session_lifetime = timedelta(days=12)

# Supabase connection — lazy initialization to avoid crashing at import time
_supabase_client = None


def get_supabase():
    """Get or create the Supabase client (lazy initialization)."""
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY environment variables must be set. "
                f"Got URL={'set' if url else 'empty'}, KEY={'set' if key else 'empty'}"
            )
        _supabase_client = create_client(url, key)
    return _supabase_client


# Define a home route (/)

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

        try:
            get_supabase().table("users").insert({
                "username": username,
                "password": password
            }).execute()
        except Exception as e:
            print(f"Error inserting user: {e}")

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
        try:
            get_supabase().table("users").delete().eq("username", username).execute()
        except Exception as e:
            print(f"Error deleting user: {e}")
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
            try:
                existing = get_supabase().table("notes").select("id").eq("title", title).execute()
                if not existing.data:
                    get_supabase().table("notes").insert({
                        "title": title,
                        "note": note
                    }).execute()
            except Exception as e:
                print(f"Error creating note: {e}")

    return redirect("/todos")


# Define a todos route

@app.route("/todos")
def todos():
    try:
        result = get_supabase().table("notes").select("*").order("id").execute()
        rows = [(row["id"], row["title"], row["note"]) for row in result.data]
    except Exception as e:
        print(f"Error fetching notes: {e}")
        rows = []
    return render_template("todos.html", todos=rows)


# Define a delete route for deleting a todo when a user wants to

@app.route("/delete", methods=["POST"])
def delete():
    delete_id = request.form.get("final_delete")
    if delete_id:
        try:
            get_supabase().table("notes").delete().eq("id", int(delete_id)).execute()
        except Exception as e:
            print(f"Error deleting note: {e}")
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
            try:
                get_supabase().table("notes").update({
                    "title": updatedTitle,
                    "note": updatedText
                }).eq("id", int(note_id)).execute()
            except Exception as e:
                print(f"Error updating note: {e}")

    return redirect('/todos')
