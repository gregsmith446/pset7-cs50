# imports
import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd

# Configure flask application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure user responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom jinja filter converts stock data into USD format
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
# db is now equal to finance.db
db = SQL("sqlite:///finance.db")

# user's home page - requires login
@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # look up the current user
    users = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])
    stocks = db.execute(
            "SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0", user_id=session["user_id"])
    quotes = {}

    for stock in stocks:
        quotes[stock["symbol"]] = lookup(stock["symbol"])

    cash_remaining = users[0]["cash"]
    total = cash_remaining

    return render_template("portfolio.html", quotes=quotes, stocks=stocks, total=total, cash_remaining=cash_remaining)

# user's buy page - requires login
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    return apology("TODO")


# user's history page - requires login
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


# login page
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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

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

# log out page
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# user's get quote page - requires login
@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    return apology("TODO")


# user registration page
@app.route("/register", methods=["GET", "POST"])
def register():

    # submit user's input via POST to /register
    # when the request method is POST, aka the user attempting to register
    # follow this logic
    if request.method == "POST":

        # require a username, no blank fields
        if not request.form.get("username"):
            return apology("Must Provide Username")

        # require a password, no blank fields
        elif not request.form.get("password"):
            return apology("Must Provide Password")

        # require that password matches verified password
        elif request.form.get("password") != request.form.get("passwordagain"):
            return apology("Passwords must be Identical")

        # once at this step, registration data is valid
        # INSERT the new user into users, storing a hash of the user's password (not the password)
        result = db.execute("INSERT INTO users (username, hash) \
                            VALUES(:username, :hash)", \
                            username=request.form.get("username"), \
                            hash = generate_password_hash(request.form.get("password")))

        if not result:
            return apology("username already exists, pick different one or login with existing account")

        # log user in automatically when successfully registered
        session["user_id"] = result

        # redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")

    # when this is done, you will be able to login + logout with new registered user
    # Can see the new rows in phpLITEadmin

# user sell page - login required
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")

# error handler to be used in application.py
def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
