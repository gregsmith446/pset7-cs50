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

    totalPrice=0
    portfolio = db.execute("SELECT * FROM portfolio WHERE id=:id", id=session["user_id"])
    user = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])

    for row in portfolio:
        # print(row)
        updatedInfo = lookup(row["symbol"])
        db.execute("UPDATE portfolio SET 'price' = :u WHERE symbol = :s", u=updatedInfo['price'], s=row["symbol"])

    portfolio = db.execute("SELECT * FROM portfolio WHERE id=:id", id=session["user_id"])

    for row in portfolio:
        totalPrice += row["price"] * row["shares"]
    # print(user[0])
    return render_template("index.html", portfolio=portfolio, usd=usd, user=user[0], totalPrice=totalPrice)

# user's buy page - requires login
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    #if user gets to page via POST by submitting a form
    if request.method == "POST":
        # immediately set quote == to stock symbol in form
        quote = lookup(request.form.get("symbol"))

        # require user input a stock symbol
        # render apology if input blank or symbol does not exist
        if quote == None:
            return apology("invalid symbol", 400)

        # require a user input a # of shares to buy
        # render apology if input not a positive INT
        try:
            shares = int(request.form.get("shares"))
        except:
            return apology("you must buy more than 1 or more shares", 400)

        if shares <= 0:
            return apology("cannot buy less than 1 shares", 400)

        # find username in DB --> users
        rows = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])

        # Select how much cash the user currently has in users
        # Set vars == cash in account + price per share
        cash_remaining = rows[0]["cash"]
        price_per_share = quote["price"]

        # calculate price of requested shares
        # call lookup to see stock's current price
        total_price = price_per_share * shares

        # render apology w/o completing a purchase if user cannot afford # of shares requested @ current price
        if total_price > cash_remaining:
            return apology("not enough funds")

        # add 1 or more tables to finance.db to keep track of purchase
        # define unique indexes on any field that should be unique
        # define non-Unique indexes on any field via which you will search
        # will be able to see user's purchases in new tables via phpliteadmin
        db.execute("UPDATE users SET cash = cash - :price WHERE id = :user_id", price=total_price, user_id=session["user_id"])
        # new_user_id = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",

        db.execute("INSERT INTO portfolio (id, symbol, price, shares) VALUES(:user_id, :symbol, :price, :shares)",
            user_id=session["user_id"],
            symbol=request.form.get("symbol"),
            shares=request.form.get("shares"),
            price=price_per_share)

        flash("Bought!")

        return redirect(url_for("index"))

    else:
        return render_template("buy.html")

# user's history page - requires login
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    transactions = db.execute("SELECT * from portfolio where id=:id", id=session["user_id"])

    for row in transactions:
        print(row)
        return render_template("history.html", transactions=transactions)


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

    #if user gets to page via POST by submitting a form
    if request.method == "POST":
        # use the lookup() helper function to get the stock quote
        # lookup(), given a stock symbol, returns a stock quote in the form of a dict'
        # contacts yahoo finance API, gets response, parse response into: name, price, symbol.
        quote = lookup(request.form.get("symbol"))

        # if there is no stock match
        if quote == None:
            return apology("not a valid symbol", 400)

        # if there is, set quote == quote + render the quoted.html page
        # that page has the requested quote data
        return render_template("quoted.html", quote=quote)

    else: # the user reached route via GET, send them back to the page to request a quote
        return render_template("quote.html")


# user registration page
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password and confirmation, 'passwordagain' match
        elif not request.form.get("password") == request.form.get("passwordagain"):
            return apology("passwords do not match", 400)

        # hash the password and insert a new user into the database
        hash = generate_password_hash(request.form.get("password"))
        new_user_id = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
        username=request.form.get("username"), hash=hash)

        # if username already exists, return apology
        if not new_user_id:
            return apology("username taken", 400)

        # Remember which user has logged in
        session["user_id"] = new_user_id

        # Display a flash message
        flash("Registered!")

        # Redirect user to home page
        return redirect(url_for("index"))

    # User reached route via GET, not POST (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

# user sell page - login required
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        portfolio = db.execute("SELECT * FROM portfolio WHERE id=:id", id=session["user_id"])
        print(portfolio)
        for stock in portfolio:
            print(stock)
            if stock["symbol"] == symbol:
                if stock["shares"] > 1 and stock["shares"] > shares:
                    db.execute("UPDATE portfolio SET 'shares'=shares-:sh where symbol=:s", sh=shares, s=symbol)
                elif stock["shares"] == 1:
                    db.execute("DELETE FROM portfolio WHERE symbol=:s", s=symbol)

        return redirect("/")
    else:
        return render_template("sell.html")

# error handler to be used in application.py
def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
