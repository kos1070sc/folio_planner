from app import app
from flask import render_template, request, redirect, url_for, session, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
from app.forms import LoginForm, CreateAccount, CreateNew
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

    
    
@app.route('/create_account',  methods=["GET", "POST"])
def create_account():
    form = CreateAccount() #get the form thingy 
    #check entered meets the requirements 
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
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
            print("yes")
            # store username and hashed password, admin previlege = 0 (normal user)
            new_user = models.User(name=username, privilege=0)
            new_user.set_password(password)
            #commit to the database
            db.session.add(new_user)
            db.session.commit()
            flash("Account created please login")
            return redirect(url_for("login"))
    return render_template("create_account.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm() #get the form thingy 
    #check entered meets the requirements 
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
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
            return redirect(url_for("dashboard", user_id=session["user_id"]))
        else:
            flash("⚠️ Incorrect name or password")
            return redirect(url_for('login'))
    else:
        return render_template('login.html', form=form)
    


@app.route("/create_new", methods=["GET", "POST"])
def create_new():
    form = CreateNew()
    session_user_id = session.get("user_id")
    # if there is not user id - redirect user to login
    if not user_id:
        flash("Please login first")
        return redirect(url_for("login"))
    if form.validate_on_submit():
        theme = form.theme.data
        #check is user has entered a theme
        if theme:
            print(theme)
            #creates new folio in database with the theme entered
            new_folio = models.Folio(theme=theme, user_id=user_id)
            db.session.add(new_folio)
            db.session.commit()

            # creates 3 panels with panel_number 1 to 3 
            # puts inside a list and added to database
            panels = []
            for i in range(1,4):
                panel = models.Panel(folio_id = new_folio.id,
                             user_id = session_user_id,
                             panel_number = i)
                panels.append(panel)
                db.session.add(panel)
                db.session.commit()

            # creates 21 paintings with pos

            # let user edit their newly created folio
            # passes on the folio object as well
            return render_template("edit_folio.html", user_id=session_user_id, folio=new_folio)
        # display an error message if no theme
        else:
            flash("⚠️ Please enter a theme")
            return render_template("create_new.html", form=form, user_id=user_id)

    return render_template("create_new.html", form=form, user_id=user_id)
    

@app.route("/my_folios/<int:user_id>")
def my_folios(user_id):
    # get the user id 
    session_user_id = session.get("user_id")
    # if there is not user id - redirect user to login
    if not session_user_id:
        flash("Please login first")
        return redirect(url_for("login"))
    # check if session id matches id in url
    elif session_user_id != user_id:
        flash("You can only view your own folios")
        return redirect(url_for("dashboard", user_id = session_user_id))
    else:
        folio = models.Folio.query.filter_by(user_id=user_id)
    # need to pass user_id to my_folios.html for user_layout.html to use 
        return render_template("my_folios.html", folio=folio, user_id=user_id)
    
@app.route("/dashboard/<int:user_id>")
def dashboard(user_id):
    # get the user id 
    session_user_id = session.get("user_id")
    # if there is not user id - redirect user to login
    if not session_user_id:
        flash("Please login first")
        return redirect(url_for("login"))
    # check if session id matches id in url
    elif session_user_id != user_id:
        flash("You can only view your own dashboard")
        return redirect(url_for("dashboard", user_id = session_user_id))
    else:
        user_info = models.User.query.get(session['user_id'])
        return render_template("dashboard.html", user_info=user_info, user_id=user_id)
    
@app.route("/edit_folio/<int:user_id>/<int:folio_id>")
def edit_folio(user_id, folio_id):
    session_user_id = session.get("user_id")
    # check if logged in
    if not session_user_id:
        flash("⚠️ Please log in to edit a folio")
        return redirect(url_for("login"))
    
    # get all info from that user based on their id from URL
    user = db.session.get(models.User, user_id)
    # If user doesn't exist show error message and redirect to dashboard
    if not user:
        flash("⚠️ User not found")
        return redirect(url_for("dashboard"))

    # Get folio info by id in the url 
    # 404 if not found
    folio = models.Folio.query.get_or_404(folio_id)
    # Verify if that folio belong to the user
    if session_user_id != folio.user_id:
        flash("⚠️ You can only edit your own folio")
        return redirect(url_for("dashboard", user_id = session_user_id))

    # get all paintings from that folio and order them by their position 
    paintings = models.Painting.query.filter_by(folio_id=folio_id).order_by(models.Painting.position).all()
    return render_template("edit_folio.html", user_id = session_user_id, paintings=paintings, folio=folio)
    # Query the database for image paths 

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('root'))