# Import all the neccessary libraries

import sqlite3
from flask import Flask, render_template, request, redirect, session
from datetime import timedelta

# Set up the app with Flask function and secret key, and also specify the session lifetime

app = Flask(__name__)
app.secret_key = "DIGINOTES_12345"
app.permanent_session_lifetime = timedelta(days=12)

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
  # If request method is GET, render account.html as template
  if request.method == "GET":
    return render_template("account.html")
  # If request method is POST, start checking whether user has entered all the data
  else:
    # Grab the username and password from the submitted HTML form
    username = request.form.get("username")
    password = request.form.get("password")

    # If username field is blank, show an error by rendering the account.html with an error message passed
    # in to message1
    if not username:
      return render_template("account.html", message1="Missing username")
    # If passsword field is blank, show an error by rendering the account.html with an error message passed
    # in to message2
    elif not password:
      return render_template("account.html", message2="Missing password")
    
    # Set session to permanent and store the username as a cookie
    session.permanent = True
    session["username"] = username

    # Establish a SQLite 3 connection and insert the user's username amd password
    conn = sqlite3.connect("diginotes.db")
    cursor = conn.cursor() 
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))

    # Commit the changes to the database and close the connection
    conn.commit()
    conn.close()

  # Redirect to the user's dashboard since they are signed in
  return redirect("/")

# Define a dashboard route

@app.route("/dashboard")
def dashboard():
  # Specify that if the username is not stored as a cookie, they should be redirected to home page
  if "username" not in session:
    return redirect("/")
  # If the user is signed in, then show them their dashboard
  else:
    return render_template("dashboard.html", username=session["username"])

# Specify a sign out route

@app.route("/sign_out")
def sign_out():
  # Establish a SQLite3 connection
  conn = sqlite3.connect("diginotes.db")
  cursor = conn.cursor()

  # Delete the user's account credentials and clear all cookies
  cursor.execute("DELETE FROM users WHERE username = ?", (session["username"],))  
  session.clear()

  # Redirect the user to home page
  return redirect("/")

# Define a landing route which is for the home icon on the dashboard

@app.route("/landing")
def landing():
  # Render the main.html as template
  return render_template("main.html")

# Now define a route which will enable users to create todos

@app.route("/todo", methods=["GET", "POST"])
def todo():
  # If request method is GET, render todo.html as template
  if request.method == "GET":
    return render_template("todo.html")
  else:
    # Grab the title and note values from the submitted HTML form
    title = request.form.get("title")
    note = request.form.get("text")

    # If title field is blank, render the todo.html with an error message passed in to message1
    if not title:
      return render_template("todo.html", message1="Hey, what will you call your to-do?")
    # If note field is blank, render the todo.html with an error message passed in to message2
    elif not note:
      return render_template("todo.html", message2="What task do you want to finish? Not none, right?")
    # Else, if all is filled up, establish a SQLite3 connection
    else:
      conn = sqlite3.connect("diginotes.db")
      cursor = conn.cursor()

      # Try inserting the title and note and if an IntegrityError occurs, pass
      try:
        cursor.execute("INSERT INTO notes (title, note) VALUES (?, ?)", (title, note))
      except sqlite3.IntegrityError:
        pass
      # Commit changes to the database and then close the connection
      conn.commit()
      conn.close()

    # Redirect to the todos route, which will show the user their stored todos
    return redirect("/todos")

# Define a todos route

@app.route("/todos")
def todos():
  # Establish a SQLite3 connection
  conn = sqlite3.connect("diginotes.db")
  cursor = conn.cursor()
  # Grab all the data from the notes table
  cursor.execute("SELECT * FROM notes;")

  # Store the data in the rows variable
  rows = cursor.fetchall()
  
  # Close the connection, and pass the rows variable to the todos while rendering template
  conn.close()
  return render_template("todos.html", todos=rows)

# Define a delete route for deleting a todo when a user wants to 

@app.route("/delete", methods=["POST"])
def delete():
  # Grab the delete id from the submitted form
  delete = request.form.get("final_delete")
  
  # Establish the database connection
  conn = sqlite3.connect("diginotes.db")
  cursor = conn.cursor()
  # Delete the row from notes table where the id matches the value of the delete table
  cursor.execute("DELETE FROM notes WHERE id = ?", (delete,))

  # Commit the changes and close the connection, and redirect to the /todos route
  conn.commit()
  conn.close()
  return redirect("/todos")

# Define an update route, which will update the note at user's will

@app.route("/update", methods=["GET", "POST"])
def update():
  # If request method is GET, grab the value of the update variable from the submitted form
  # and then store it in a cookie, and render update.html as template
  if request.method == "GET":
    update = request.args.get("update")
    session["note_id"] = update
    return render_template("update.html")
  # If request method is POST, then grab the values of title and note text to modify
  else:
    updatedTitle = request.form.get("updated_title")
    updatedText = request.form.get("updated_text")

    # Establish a SQLite3 database connection
    conn = sqlite3.connect("diginotes.db")
    cursor = conn.cursor()

   # Update the notes by modifying the note title and text, where the id matches the id stored in the cookie earlier 
    cursor.execute("UPDATE notes SET title = ?, note = ? WHERE id = ?", (updatedTitle, updatedText, session["note_id"]))

  # Commit the changes, close the connection and redirect to /todos
    conn.commit()
    conn.close()
  return redirect('/todos')

