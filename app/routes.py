from app import app
from flask import render_template, request, redirect, url_for, session, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
import os
import secrets
app.secret_key = secrets.token_hex(32)
# Creates a random key that is 64 characters long to encrypt session data
# This makes more secure and protects against seesion hijacking 
from werkzeug.security import generate_password_hash, check_password_hash



basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, "folio.db")
db.init_app(app)

import app.models as models

def set_password(self, password):
    self.password = generate_password_hash(password, method='pbkdf2:sha256', salt_length = 8)
    #This function hashes the password before storing it
    #It uses PBKDF2-SHA256 password hasher with 8 byte salt 
    #This means that the hashed password will always be 60 characters long

def check_password(self, password):
    return check_password_hash(self.password, password)
    #This compares the password to the stored hash to check if a password is correct
    #If it mathes it will return True if not then False 

@app.route('/')
def root():
    return render_template('home.html')


@app.route('/colour')
def colour():
    colours = models.Colour.query.all()
    return render_template("colour.html", colours=colours)

@app.route('/create_account')
def create_account():
    #create account page
    return render_template('create_account.html')
    


@app.route('/submit_create_account',  methods=["POST"])
def create_account_submit():
    print("fish")
    username = request.form['username']
    password = request.form['password']
    #gets username and password from html form
    new_user = models.User(name=username, privilege=0)
    set_password(password)
    #creates a new user with no admin privileges and stores the hashed password
    db.session.add(new_user)
    db.session.commit()
    #commit to the database
    #.add prepares the data 
    #.commit actually saves it 

    return render_template_string('''Account created please login .<a href=
                                    "http://127.0.0.1:5000/form"''')
