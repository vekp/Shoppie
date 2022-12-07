import os

# import sqlite3
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:////home/vekp/mysite/database.db")



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # Queries and displays all lists assigned to current userid
    if request.method == "GET":
        """Show lists"""
        session["lists"] = (db.execute("""
        SELECT lists.id, listname, SUM(CASE WHEN crossed = 0 THEN 1 ELSE 0 END) AS qty
          FROM lists
     LEFT JOIN items
            ON items.list_id = lists.id
         WHERE user_id = ?
      GROUP BY lists.id""", session["user_id"]))

      # Query for lists shared with user
        session["shared"] = (db.execute("""
        SELECT lists.id, listname, SUM(CASE WHEN crossed = 0 THEN 1 ELSE 0 END) AS qty
          FROM lists
     LEFT JOIN items ON items.list_id = lists.id
          JOIN shares ON shares.list_id = lists.id
         WHERE shares.user_id = ?
      GROUP BY lists.id""", session["user_id"]))
        return render_template("lists.html", lists=session["lists"], shared=session["shared"])


@app.route("/add_list", methods=["POST"])
@login_required
def add_list():
    listname = request.form.get("listname")
    lists = db.execute("SELECT * FROM lists WHERE user_id = ?", session["user_id"])

    # Check if list of same name already exists
    if any(list["listname"] == listname for list in lists):
        flash("List not added - already exists.")
        return redirect("/")

    # Insert new list into database
    session["listname"] = listname
    session["list_id"] = db.execute("INSERT INTO lists (user_id, listname) VALUES (?, ?)", session["user_id"], session["listname"])
    flash("New list added.")
    return redirect("/")


@app.route("/edit_list", methods=["GET", "POST"])
@login_required
def edit_list():
    if request.method == "GET":
        if request.args.get("list_id"):
            session["list_id"] = request.args.get("list_id")
        list = db.execute("SELECT * FROM lists WHERE id = ?", session["list_id"])

        # Check list belongs to user
        if list[0]["user_id"] != session["user_id"]:
            flash("Access denied.")
            return redirect("/")

        # Query list's shared users
        shared = db.execute("""
        SELECT shares.id, users.username
          FROM shares
          JOIN users ON shares.user_id = users.id
         WHERE list_id = ?
      ORDER BY users.username""", session["list_id"])
        return render_template("edit_list.html", list=list[0], shared=shared)

    if request.method == "POST":
        list_id = int(request.form.get("list_id"))

        # Validate user
        if not any (list_id == list['id'] for list in session["lists"]):
            flash("Access denied.")
            return redirect("/")

        # Update list name
        db.execute("UPDATE lists SET listname = ? WHERE id = ?", request.form.get("listname"), list_id)
        flash("List updated")
        return redirect("/edit_list")


@app.route("/delete_list", methods=["POST"])
@login_required
def delete_list():
    list_id = int(request.form.get("list_id"))

    # Validate user
    if not any (list_id == list['id'] for list in session["lists"]):
        flash("Access denied.")
        return redirect("/")

    # Delete list and related items and shares
    db.execute("DELETE FROM items WHERE list_id = ?" , list_id)
    db.execute("DELETE FROM lists WHERE id = ?", list_id)
    db.execute("DELETE FROM shares WHERE list_id = ?", list_id)
    flash("List deleted.")
    return redirect("/")


@app.route("/share", methods=["POST"])
@login_required
def share():
    list_id = int(request.form.get("list_id"))

    # Validate user
    if not any (list_id == list['id'] for list in session["lists"]):
        flash("Access denied.")
        return redirect("/")

    share = request.form.get("share")
    row = db.execute("SELECT * FROM users WHERE username = ?", share)

    # Validate entered username
    if not row:
        flash("User not found.")
        return redirect("/edit_list")
    share_id = row[0]["id"]
    if share_id == session["user_id"]:
        flash("Cannot share with yourself.")
        return redirect("/edit_list")
    if db.execute("SELECT * FROM shares WHERE list_id = ? AND user_id = ?", list_id, share_id):
        flash("Already shared.")
        return redirect("/edit_list")

    # Validation successful, create new share
    db.execute("INSERT INTO shares (list_id, user_id) VALUES (?, ?)", list_id, share_id)
    flash("List shared.")
    return redirect("/edit_list")


@app.route("/share_delete", methods=["POST"])
@login_required
def share_delete():
    share_id = request.form.get("id")

    # Validate user
    row = db.execute("""
    SELECT shares.id
      FROM shares
      JOIN lists ON shares.list_id = lists.id
     WHERE lists.user_id = ? AND shares.id = ?
     """, session["user_id"], share_id)
    if len(row) != 1:
        flash("Access denied.")
        return redirect("/")

    # Remove share
    db.execute("DELETE FROM shares WHERE id = ?", share_id)
    flash("User removed.")
    return redirect("/edit_list")


@app.route("/items", methods=["GET"])
@login_required
def items():
    if request.args.get("list_id") and request.args.get("listname"):
        session["listname"] = request.args.get("listname")
        session["list_id"] = int(request.args.get("list_id"))

    # Validate user
    if not any (session["list_id"] == list['id'] for list in session["lists"] + session["shared"]):
        flash("Access denied.")
        return redirect("/")

    # Query item list, calculate priority
    items = db.execute("""
      SELECT *, (JULIANDAY(required) - JULIANDAY(DATE()))
          AS "priority"
        FROM items
       WHERE list_id = ?
         AND crossed = 0
    ORDER BY name
    """, session["list_id"])

    # Set priority for each item
    for item in items:
        if not item["required"]:
            item["priority"] = 10
        else:
            item["priority"] = int(item["priority"])

    # Get crossed out items
    crossed = db.execute("""
      SELECT *
        FROM items
       WHERE list_id = ?
         AND crossed = 1
    ORDER BY name
    """, session["list_id"])

    # Check if list is user's own, or shared
    own = any (session["list_id"] == list['id'] for list in session["lists"])

    return render_template("items.html", items=items, crossed=crossed, listname=session["listname"], list_id=session["list_id"], own=own)


@app.route("/add_item", methods=["POST"])
@login_required
def add_item():
    name = request.form.get("item_name")
    list_id = int(request.form.get("list_id"))

    # Validate user
    if not any(list_id == list['id'] for list in session["lists"] + session["shared"]):
        flash("Access denied.")
        return redirect("/")

    items = db.execute("""
    SELECT * FROM items
        WHERE list_id = ?""", list_id)

    # Check if item already in list
    if any(item["name"] == name for item in items):
        flash("Item not added - already exists in this list.")
        return redirect("/items")

    # Add to database
    db.execute("INSERT INTO items (list_id, name) VALUES(?, ?)", list_id, name)
    flash("Item added.")
    return redirect("/items")

@app.route("/edit_item", methods=["GET", "POST"])
@login_required
def edit_item():
    if request.method == "GET":
        session["item_id"] = request.args.get("item_id")
        item = db.execute("SELECT * FROM items WHERE id = ?", session["item_id"])

        # Check items is in user's own lists or lists shared with user
        if not item or not any(item[0]["list_id"] == list["id"] for list in session["lists"] + session["shared"]):
                flash("Access denied.")
                return redirect("/")

        return render_template("edit_item.html", item=item[0])

    # Update item's values in database
    if request.method == "POST":
        name = request.form.get("item_name")
        qty = request.form.get("item_qty")
        required = request.form.get("required")
        db.execute("UPDATE items SET name = ?, quantity = ?, required = ? WHERE id = ?", name, qty, required, session["item_id"])
        flash("Item updated.")
        return redirect("/items")


@app.route("/delete_item", methods=["POST"])
@login_required
def delete_item():
    db.execute("DELETE FROM items WHERE id = ?", session["item_id"])
    flash("Item deleted.")
    return redirect("/items")


@app.route("/cross", methods=["POST"])
@login_required
def cross():
    # Toggle crossed value and clear required date
    db.execute("""UPDATE items SET crossed = NOT crossed, required = NULL WHERE id = ?""", request.form.get("item_id"))
    return redirect("/items")


@app.route("/instructions", methods=["GET"])
def instructions():
    return render_template("instructions.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("You must provide username")
            return render_template("/login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("You must provide password")
            return render_template("/login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username and/or password")
            return render_template("/login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        users = db.execute("SELECT username FROM users")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        # Ensure username was submitted
        if not username:
            flash("Username required")
            return redirect("/register")
        # Ensure unique username
        elif any(user["username"] == username for user in users):
            flash("Username already exists.")
            return redirect("/register")
        # Ensure password was submitted
        elif not password or not confirmation:
            flash("Must provide password and confirmation.")
            return redirect("/register")
        # Ensure pw and conf match
        elif password != confirmation:
            flash("Password and confirmation must match.")
            return redirect("/register")
        # success:
        else:
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, generate_password_hash(password))
            rows = db.execute("SELECT * FROM users WHERE username = ?", username)
            session["user_id"] = rows[0]["id"]
            flash("Registration successful!")
            return redirect("/")

    else:
        return render_template("register.html")
