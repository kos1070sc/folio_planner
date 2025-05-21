from app import app
from flask import render_template, request, redirect, url_for, session, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
import os
import secrets
# Creates a random key that is 64 characters long to encrypt session data
# This makes more secure and protects against seesion hijacking 
app.secret_key = secrets.token_hex(32)

basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, "folio.db")
db.init_app(app)

import app.models as models

@app.route('/')
def root():
    return render_template('root.html')


@app.route('/colour')
def colour():
    colours = models.Colour.query.all()
    return render_template("colour.html", colours=colours)

@app.route('/create_account')
def create_account():
    return render_template('create_account.html')
    
    
@app.route('/submit_create_account',  methods=["POST"])
def create_account_submit():
    #get username and password from html form
    username = request.form['username']
    password = request.form['password']
    #checks if the user has entered both a username and password
    if not username or not password:
        flash("⚠️ Please enter a user and password")
        return redirect(url_for("create_account"))
    #checks if username is already in the database
    #queries the database for the first match
    elif models.User.query.filter_by(name=username).first():
        flash("⚠️ Usermame already exist. Please choose another one")
        return redirect(url_for("create_account"))
    else:
        # store username and hashed password, admin previlege = 0 (normal user)
        new_user = models.User(name=username, privilege=0)
        new_user.set_password(password)
        #commit to the database
        db.session.add(new_user)
        db.session.commit()

    return render_template_string('''Account created please login .<a href=
                                    "http://127.0.0.1:5000"''')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        #checks if the user has entered both a username and password
        if not username or not password:
            flash("⚠️ Please enter a username and a password")
            return redirect(url_for('login'))
        #looks for the user in the database 
        user = models.User.query.filter_by(name=username).first()
        #check if username and passwords matches with database
        if user and user.check_password(password):
            #create session 
            session['user_id'] = user.id
            session['user_name'] = user.name
            print(session)
            return redirect(url_for("dashboard"))
        else:
            flash("⚠️ Incorrect name or password")
            return redirect(url_for('login'))
    else:
        return render_template('login.html')
    
    
@app.route('/dashboard')
def dashboard():
    #check if user has logged in 
    #if not return them to the login page
    if 'user_id' not in session:
        return redirect(url_for('login'))
    else:
        account_info = models.User.query.get(session['user_id'])
        print(account_info)
        return render_template('dashboard.html', account_info=account_info)

@app.route("/planner")
def planner():
    return render_template("planner.html")
