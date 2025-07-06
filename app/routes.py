from app import app
from flask import render_template, request, redirect, url_for, session, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from app.forms import LoginForm, CreateAccount, CreateNew, ImageUpload, DeleteImage, MyFolio
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
    form = CreateAccount()  # get the form thingy
    # check entered meets the requirements
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
    # checks if the user has entered both a username and password
        if not username or not password:
            flash("⚠️ Please enter a user and password", "error")
            return redirect(url_for("create_account"))
        # checks if username is already in the database
        # queries the database for the first match
        elif models.User.query.filter_by(name=username).first():
            flash("⚠️ Usermame already exist. Please choose another one", "error")
            return redirect(url_for("create_account"))
        else:
            print("yes")
            # store username and hashed password
            # admin previlege = 0 (normal user)
            new_user = models.User(name=username, privilege=0)
            new_user.set_password(password)
            # commit to the database
            db.session.add(new_user)
            db.session.commit()
            flash("Account created please login", "success")
            return redirect(url_for("login"))
    return render_template("create_account.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()  # get the form thingy
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        # checks if the user has entered both a username and password
        if not username or not password:
            flash("⚠️ Please enter a username and a password", "error")
            return redirect(url_for('login'))
        # looks for the user in the database
        user = models.User.query.filter_by(name=username).first()
        # check if username and passwords matches with database
        if user and user.check_password(password):
            # create session
            # store id and name in session
            session['user_id'] = user.id
            session['user_name'] = user.name
            return redirect(url_for("dashboard", user_id=session["user_id"]))
        else:
            flash("⚠️ Incorrect name or password", "error")
            return redirect(url_for('login'))
    else:
        return render_template('login.html', form=form)


@app.route("/create_new", methods=["GET", "POST"])
def create_new():
    form = CreateNew()
    session_user_id = session.get("user_id")
    # if there is not user id - redirect user to login
    if not session_user_id:
        flash("Please login first", "error")
        return redirect(url_for("login"))
    if form.validate_on_submit():
        theme = form.theme.data
        # check is user has entered a theme
        if theme:
            print(theme)
            # creates new folio in database with the theme entered
            new_folio = models.Folio(theme=theme, user_id=session_user_id)
            db.session.add(new_folio)
            db.session.commit()

            # creates 3 panels with panel_number 1 to 3
            # puts inside a list and added to database
            for i in range(1, 4):
                panel = models.Panel(folio_id=new_folio.id,
                                     user_id=session_user_id,
                                     panel_number=i)
                db.session.add(panel)
            db.session.commit()

            # creates 21 paintings with positions 1 to 21
            for i in range(1, 22):
                # paintings have different due dates
                # these need to be assigned outside the model instuctor call
                if i < 8:
                    term_number = 1
                elif 7 < i < 15:
                    term_number = 2
                else:
                    term_number = 3
                if i in [1, 2, 3, 8, 9, 15, 16]:
                    week_number = 3
                elif i in [4, 5, 10, 11, 12, 17, 18, 19, 20]:
                    week_number = 6
                else:
                    week_number = 10
                if i in [4, 5, 8, 9, 11]:
                    composition_assignment = "A4 Landscape"
                elif i in [1, 2, 3, 6]:
                    composition_assignment = "A4 Portrait"
                elif i == 7:
                    composition_assignment = "A3 Landscape"
                elif i in [13, 14]:
                    composition_assignment = "A3 Portrait"
                elif i in [15, 16]:
                    composition_assignment = "A3 Square"
                elif i in [10, 12, 17, 18, 19, 20]:
                    composition_assignment = "A5 Portrait"
                else:
                    composition_assignment = "Wide A3 Landscape"
                painting = models.Painting(
                    folio_id=new_folio.id,
                    user_id=session_user_id,
                    position=i,
                    title="Untitled painting",
                    term_due=term_number,
                    week_due=week_number,
                    composition=composition_assignment,
                    image=None
                )
                # send to database
                db.session.add(painting)
            db.session.commit()
            # let user edit their newly created folio
            # passes on the folio object as well
            return redirect(url_for("edit_folio",
                                    user_id=session_user_id,
                                    folio_id=new_folio.id))

        # display an error message if no theme
        else:
            flash("⚠️ Please enter a theme", "error")
            return render_template("create_new.html",
                                   form=form,
                                   user_id=session_user_id)
    return render_template("create_new.html",
                           form=form,
                           user_id=session_user_id,
                           )


@app.route("/my_folios/<int:user_id>", methods=["GET", "POST"])
def my_folios(user_id):
    delete_form = MyFolio()
    folio_id = request.form.get("folio_id")
    # get the user id
    session_user_id = session.get("user_id")
    # delete folio
    if delete_form.validate_on_submit():
        # get folio object
        folio = models.Folio.query.get(folio_id)
        # check if folio exists and belongs to user
        if folio and folio.user_id == session_user_id:
            # delete all paintings within that folio first
            paintings = models.Painting.query.filter_by(folio_id=folio_id)
            for painting in paintings:
                db.session.delete(painting)
            # then delete the folio
            db.session.delete(folio)
            # commit database
            db.session.commit()
            flash(f"{folio.theme} folio delete successfully", "success")
            return redirect(url_for("my_folios", user_id=session_user_id))
        else:
            flash("Error: Folio not found or access denied", "error")
            return redirect(url_for("my_folios", user_id=session_user_id))
    # if there is not user id - redirect user to login
    if not session_user_id:
        flash("Please login first", "error")
        return redirect(url_for("login"))
    # check if session id matches id in url
    elif session_user_id != user_id:
        flash("You can only view your own folios", "error")
        return redirect(url_for("dashboard", user_id=session_user_id))
    else:
        folio = models.Folio.query.filter_by(user_id=user_id)
    # need to pass user_id to my_folios.html for user_layout.html to use
        return render_template("my_folios.html",
                               folio=folio,
                               user_id=user_id,
                               delete_form=delete_form,
                               folio_id=folio_id)


@app.route("/dashboard/<int:user_id>")
def dashboard(user_id):
    # get the user id
    session_user_id = session.get("user_id")
    # if there is not user id - redirect user to login
    if not session_user_id:
        flash("Please login first", "error")
        return redirect(url_for("login"))
    # check if session id matches id in url
    elif session_user_id != user_id:
        flash("You can only view your own dashboard", "error")
        return redirect(url_for("dashboard", user_id=session_user_id))
    else:
        user_info = models.User.query.get(session['user_id'])
        return render_template("dashboard.html",
                               user_info=user_info,
                               user_id=user_id)


@app.route("/edit_folio/<int:user_id>/<int:folio_id>", methods=['GET', 'POST'])
def edit_folio(user_id, folio_id):
    form = ImageUpload()
    delete_form = DeleteImage()
    session_user_id = session.get("user_id")
    painting_id = request.form.get("painting_id")
    # check if logged in
    if not session_user_id:
        flash("⚠️ Please log in to edit a folio", "error")
        return redirect(url_for("login"))
    # get all info from that user based on their id from URL
    user = db.session.get(models.User, user_id)
    # If user doesn't exist show error message and redirect to dashboard
    if not user:
        flash("⚠️ User not found", "error")
        return redirect(url_for("dashboard"))
    # Get folio info by id in the url
    # 404 if not found
    folio = models.Folio.query.get_or_404(folio_id)
    # Verify if that folio belong to the user
    if session_user_id != folio.user_id:
        flash("⚠️ You can only edit your own folio", "error")
        return redirect(url_for("dashboard", user_id=session_user_id))
    # handles delete form first to avoid accidentally processing an upload
    # check if the form being sent is actually the delete form
    if "delete_image" in request.form and delete_form.validate_on_submit():
        painting = models.Painting.query.get(painting_id)
        # get path to delete
        delete_path = f"app/{painting.image}"
        # delete the image
        os.remove(delete_path)
        # assign none to painting image to delete from database
        painting.image = None
        db.session.commit()
        flash("Image deleted successfully", "success")
        return redirect(url_for("edit_folio",
                        user_id=session_user_id,
                        folio_id=folio_id))
    # handles image upload form
    elif form.validate_on_submit():
        # grab the uploaded image file form upload file form
        file = request.files['painting_image']
        # check if there's anything uploaded
        if file.filename == "":
            flash("⚠️ No selected file", "error")
            return redirect(url_for("edit_folio",
                                    user_id=session_user_id,
                                    folio_id=folio_id))
        # funtion that checks if file is allowed

        def allowed_file(filename):
            if "." not in filename:
                return False
            # split the file name into two parts between the .
            # then get the extension
            file_extension = filename.rsplit('.', 1)[1].lower()
            # list of allowed extensions
            allowed_extensions = ['png', 'jpg', 'jpeg']
            if file_extension in allowed_extensions:
                return True
            else:
                return False
        # check if the file exists and if it has the allowed extension
        if file and allowed_file(file.filename):
            # make filename cleaner (no spaces, special chaaracters)
            # to this to block malicious filenames that could excute code
            orginal_filename = secure_filename(file.filename)
            # split the filename into two parts so that we can rename it later
            filename_part, extension_part = os.path.splitext(orginal_filename)
            # assigns a number to filename in case there is a double up
            file_number = 1
            while True:
                numbered_filename = f"{filename_part}_{file_number}{extension_part}"
                # check if this path is taken
                if os.path.exists(f"app/static/images/{numbered_filename}"):
                    # if yes file number increases by 1
                    file_number += 1
                else:
                    break
            save_path = f"app/static/images/{numbered_filename}"
            database_path = f"/static/images/{numbered_filename}"
            # save file
            file.save(save_path)
            # get painting id to update the image path
            # fetch that painting
            painting = models.Painting.query.get(painting_id)
            # update image path column
            painting.image = database_path
            db.session.commit()
            flash("Image uploaded successfully", "success")
            print(database_path)
            return redirect(url_for("edit_folio",
                                    user_id=session_user_id,
                                    folio_id=folio_id))
        else:
            flash("File type not supported", "error")


    # get all paintings from that folio and order them by their position
    paintings = models.Painting.query.filter_by(folio_id=folio_id).order_by(models.Painting.position).all()
    return render_template("edit_folio.html",
                           user_id=session_user_id,
                           paintings=paintings,
                           folio=folio,
                           form=form,
                           delete_form=delete_form)

@app.route("/edit_folio/<int:user_id>/<int:folio_id>/colour", methods=['GET', 'POST'])
def select_colour(user_id, folio_id):
    session_user_id = session.get("user_id")
    folio = models.Folio.query.get_or_404(folio_id)
    user =  models.User.query.get(user_id)
    colours = models.Colour.query.all()
    # check if logged in
    if not session_user_id:
        flash("⚠️ Please log in to edit a folio", "error")
        return redirect(url_for("login"))
    # check if user object is none 
    if not user:
        flash("⚠️ User not found", "error")
        return redirect(url_for("dashboard"))
    # check if folio object is none
    if not folio:
        flash("⚠️ Folio not found", "error")
        return redirect(url_for("dashboard"))
    # Verify if folio belongs to the user
    if session_user_id != folio.user_id:
        flash("⚠️ You can only edit your own folio", "error")
        return redirect(url_for("dashboard", user_id=session_user_id))
    return render_template("select_colour.html",
                           colours=colours,
                           folio=folio,
                           user=user,
                           user_id=session_user_id)
    
    

    



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('root'))

@app.route("/help")
def help():
    # check if user logged to know what template to use
    user_id = session.get("user_id")
    return render_template("help.html", user_logged_in=user_id, user_id=user_id)

# admin pages
@app.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    form = LoginForm()  # get the form thingy
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        # checks if the user has entered both a username and password
        if not username or not password:
            flash("⚠️ Please enter a username and a password", "error")
            return redirect(url_for('admin_login'))
        # looks for account in the database
        user = models.User.query.filter_by(name=username).first()
        # in case user is none
        if not user:
            flash("⚠️ Incorrect name or password", "error")
            return redirect(url_for('admin_login'))
        # get privilege value of the account
        privilege = user.privilege
        # check if username and passwords matches with database
        if user and user.check_password(password):
            # admin privileges is 1
            if privilege != 1:
                flash('''⚠️ This is account does not have admin privileges.
                        Please use user login''',
                        "error")
            else:
                # create session
                # store id and name with session
                session['admin_id'] = user.id
                session['admin_name'] = user.name
                return redirect(url_for("admin_dashboard"))
        else:
            flash("⚠️ Incorrect name or password", "error")
            return redirect(url_for('admin_login'))
    return render_template("admin_login.html", form=form)

@app.route("/admin/dashboard")
def admin_dashboard():
    session_admin_id = session.get("admin_id")
    # check if logged in as admin
    if not session_admin_id:
        # clear all session data in case non admin is trying this page
        session.clear()
        return redirect(url_for("root"))
    return render_template("admin_dashboard.html")

@app.route("/admin/view_users")
def admin_view_users():
    session_admin_id = session.get("admin_id")
    # check if logged in as admin
    if not session_admin_id:
        # clear all session data in case non admin is trying this page
        session.clear()
        return redirect(url_for("root"))
    users = models.User.query.all()
    return render_template("admin_users.html", users=users)


@app.route("/admin/all_folios/<int:user_id>", methods=["GET", "POST"])
def admin_view_user_folios(user_id):
    delete_form = MyFolio()
    session_admin_id = session.get("admin_id")
    user = models.User.query.get(user_id)
    folio = models.Folio.query.filter_by(user_id=user_id)
    folio_id = request.form.get("folio_id")
    if delete_form.validate_on_submit():
        # get folio object
        folio = models.Folio.query.get(folio_id)
        # check if folio exists
        if folio:
            # delete all paintings within that folio first
            paintings = models.Painting.query.filter_by(folio_id=folio_id)
            for painting in paintings:
                db.session.delete(painting)
            # then delete the folio
            db.session.delete(folio)
            # commit database
            db.session.commit()
            flash(f"{folio.theme} folio delete successfully", "success")
            return redirect(url_for("admin_view_user_folios", user_id=user_id,))
        else:
            flash("Error: Folio not found", "error")
            return redirect(url_for("admin_view_user_folios", user_id=user_id,))
    # if there is not user id - redirect user to login
    # check if logged in as admin
    if not session_admin_id:
        # clear all session data in case non admin is trying this page
        session.clear()
        return redirect(url_for("root"))
    # check if user exists
    if not user:
        flash("⚠️ User not found", "error")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_all_folios.html",
                           user=user,
                           delete_form=delete_form,
                           folio=folio)

@app.route("/admin/folio/<int:user_id>/<int:folio_id>",  methods=["GET", "POST"])
def admin_view_folio(user_id, folio_id):
    form = ImageUpload()
    delete_form = DeleteImage()
    session_admin_id = session.get("admin_id")
    painting_id = request.form.get("painting_id")
    folio = models.Folio.query.get(folio_id)
    # get all paintings from that folio and order them by their position
    paintings = models.Painting.query.filter_by(folio_id=folio_id).order_by(models.Painting.position).all()
    user = models.User.query.get(user_id)
    # check if logged in as admin
    if not session_admin_id:
        # clear all session data in case non admin is trying this page
        session.clear()
        return redirect(url_for("root"))
    # handles image delete
    # admins will not be able to upload images
    if delete_form.validate_on_submit():
        painting = models.Painting.query.get(painting_id)
        # get path to delete
        delete_path = f"app/{painting.image}"
        # delete the image
        os.remove(delete_path)
        # assign none to painting image to delete from database
        painting.image = None
        db.session.commit()
        flash("Image deleted successfully", "success")
        return redirect(url_for("admin_view_folio",
                        user_id=user_id,
                        folio_id=folio_id))
    return render_template("admin_folio.html",
                           user_id=user_id,
                           paintings=paintings,
                           folio=folio,
                           delete_form=delete_form,
                           form=form,
                           user=user)


# 404 page
@app.errorhandler(404)
def page_not_found(error):
    user_id = session.get("user_id")
    return render_template("404.html", user_logged_in=user_id, user_id=user_id)
