import os
import requests
import json

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

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

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Query to see if username already exists
        username_count = db.execute("SELECT COUNT(username) FROM users WHERE username = ?", username)
        username_count = username_count[0]["COUNT(username)"]

        if not username:
            return apology("Missing Username", 400)
        elif username_count > 0:
                return apology("Username Unavailable", 400)
        elif not password:
            return apology("Missing Password", 400)
        elif not confirmation:
            return apology("Missing Confirmation", 400)
        elif confirmation != password:
            return apology("Passwords Do Not Match", 400)

        hash = generate_password_hash(password)

        db.execute("INSERT INTO users (username, hash) VALUES (?,?)", username, hash)
        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        if request.form['button_id'] == 'Track':
            return redirect(url_for("tracker"))
        elif request.form['button_id'] == 'Set_Goals':
            return redirect(url_for("goals"))
        elif request.form['button_id'] == 'Invest':
            return redirect(url_for("invest"))

        return render_template("/index.html")
    else: 
        return render_template("/index.html")

@app.route("/tracker", methods=["GET","POST"])
@login_required
def tracker():
    # Log Expense Form
    if request.method == "POST":
        if request.form['type_id'] == 'Expense':
            desc = request.form.get('desc')
            value = request.form.get('value')
            date = request.form.get('date')
            if not desc or not value or not date:
                flash('Expense Information Missing')
            else:
                db.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?)", session["user_id"], 'Expense', desc, value, date)

        # Log Income Form
        elif request.form['type_id'] == 'Income':
            desc = request.form.get('desc')
            value = request.form.get('value')
            date = request.form.get('date')
            if not desc or not value or not date:
                flash('Income Information Missing')
            else:
                db.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?)", session["user_id"], 'Income', desc, value, date)
            
        history = db.execute("SELECT * FROM history WHERE id= ?", session["user_id"])
        exp_options = db.execute("SELECT DISTINCT desc FROM history WHERE id = ? AND type = 'Expense' AND desc <> ''", session["user_id"])
        inc_options = db.execute("SELECT DISTINCT desc FROM history WHERE id = ? AND type = 'Income' AND desc <> ''", session["user_id"])
        return render_template("/tracker.html", history=history, exp_options=exp_options, inc_options=inc_options)

    else:     
        """Show history of transactions"""
        exp_options = db.execute("SELECT DISTINCT desc FROM history WHERE id = ? AND type = 'Expense' AND desc <> ''", session["user_id"])
        inc_options = db.execute("SELECT DISTINCT desc FROM history WHERE id = ? AND type = 'Income' AND desc <> ''", session["user_id"])
        history = db.execute("SELECT * FROM history WHERE id= ?", session["user_id"])
        return render_template("/tracker.html", history=history, exp_options=exp_options, inc_options=inc_options)


@app.route("/goals", methods=["GET","POST"])
@login_required
def goals():
    # Quote API
    category = 'inspirational'
    api_url = 'https://api.api-ninjas.com/v1/quotes?category={}'.format(category)
    response = requests.get(api_url, headers={'X-Api-Key': 'UxaUlc3KcgfhmQDcyuz0ug==KLiusXojhNAfK1V0'})
    response = json.loads(response.text)

    if request.method == "POST":
        if request.form["create_goals_button"] == 'create_goals_button':
            if not request.form.get("name-goal") or not request.form.get("text-goal"):
                flash('Missing Goal Title or Goal')
                return render_template("/goals.html", response=response[0]) 
            
            for checkbox in 'cb1', 'cb2', 'cb3', 'cb4', 'cb5':
                value=request.form.get(checkbox)
                if value == None:
                    flash('Goal Does NOT Meet All SMART Requirements')
                    return render_template("/goals.html", response=response[0]) 

            title = request.form.get("name-goal")
            goal = request.form.get("text-goal")

            db.execute("INSERT INTO goals VALUES (?, ?, ?, ?)", session["user_id"], title, goal, 0)
            flash('Goal Added')
            goals = db.execute("SELECT * FROM goals WHERE id=?", session["user_id"])
            return render_template("/table_goals.html", goals=goals)

        return render_template("/goals.html", response=response[0])
    else:
        return render_template("/goals.html", response=response[0])

@app.route("/table_goals", methods=["GET","POST"])
@login_required
def table_goals():
    if request.method == "POST":
        goals = db.execute("SELECT * FROM goals WHERE id=?", session["user_id"])
        return render_template("/table_goals.html", goals=goals)
    else: 
        goals = db.execute("SELECT * FROM goals WHERE id=?", session["user_id"])
        return render_template("/table_goals.html", goals=goals)

@app.route("/invest", methods=["GET","POST"])
@login_required
def invest():
    if request.method == "POST":
        return render_template("/invest.html")
    else: 
        return render_template("/invest.html")




