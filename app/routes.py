from app import app
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import secrets
import app.models as models
app.secret_key = secrets.token_hex(32)
# Creates a random key that is 64 characters long to encrypt session data
# This makes more secure and protects against seesion hijacking 

basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, "folio.db")
db.init_app(app)

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
    if request.method == 'POST':
        username = request.form('username')
        password = request.form('password')
        #gets username and password from html form

        if models.User.query.filter_by(name = username).first():
        #queries the database and look for the first match 
        #if not matches it will return None
            flash('Username already exists')
            return redirect(url_for('login'))
            #if username matches redirects the user to login instead

        new_user = models.User(name = username, privilege = 0)
        new_user.set_password(password)
        #creates a new user with no admin privileges and stores the hashed password
        db.session.add(new_user)
        db.session.commit()
        #commit to the database
        #.add prepares the data 
        #.commit actually saves it 

        flash('Account created! Please login.')
        return redirect(url_for('login'))
    return render_template('create_account.html')
