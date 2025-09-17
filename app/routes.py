from app import app
from flask import render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from app.forms import LoginForm, CreateAccount, CreateNew, ImageUpload, DeleteImage, MyFolio
import os
import secrets
# Encrypt session data
app.secret_key = secrets.token_hex(32)

basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir,
                                                                    "folio.db")
db.init_app(app)
import app.models as models


@app.route('/')
def root():
    return render_template('root.html')


@app.route('/colour')
def colour():
    user_id = session.get("user_id")
    colours = models.Colour.query.all()
    return render_template("colour.html",
                           colours=colours,
                           user_logged_in=user_id,
                           user_id=user_id)


@app.route('/create_account',  methods=["GET", "POST"])
def create_account():
    form = CreateAccount()
    # validate username and password
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
    # check if both username and password have been entered
        if not username or not password:
            flash("⚠️ Please enter a user and password", "error")
            return redirect(url_for("create_account"))
        # see if username is already taken
        elif models.User.query.filter_by(name=username).first():
            flash("⚠️ Usermame already exist. Please choose another one",
                  "error")
            return redirect(url_for("create_account"))
        else:
            # store username and hashed password
            # previlege set to 0 (normal user)
            new_user = models.User(name=username, privilege=0)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created please login", "success")
            return redirect(url_for("login"))
    return render_template("create_account.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        # check if both username and password are entered
        if not username or not password:
            flash("⚠️ Please enter a username and a password", "error")
            return redirect(url_for('login'))
        # search for the user in the database
        user = models.User.query.filter_by(name=username).first()
        # check if username is valid and password matches
        if user and user.check_password(password):
            # create session
            # store id and name in session
            session['user_id'] = user.id
            session['user_name'] = user.name
            return redirect(url_for("dashboard"))
        else:
            flash("⚠️ Incorrect name or password", "error")
            return redirect(url_for('login'))
    else:
        return render_template('login.html', form=form)


@app.route("/create_new", methods=["GET", "POST"])
def create_new():
    form = CreateNew()
    session_user_id = session.get("user_id")
    # see if user is logged in
    if not session_user_id:
        flash("Please login first to create a new folio", "success")
        return redirect(url_for("login"))
    if form.validate_on_submit():
        theme = form.theme.data
        # check is user has entered a theme
        if theme:
            # creates new folio in database with the theme entered
            new_folio = models.Folio(theme=theme,
                                     user_id=session_user_id,
                                     # 0 = no colour pallete assigned
                                     # 1 = colour pallete assigned
                                     colour_assignment=0)
            db.session.add(new_folio)
            db.session.commit()
            # creates 3 panels with panel_number 1 to 3
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
                db.session.add(painting)
            db.session.commit()
            # redirect user to edit page after folio creation
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


@app.route("/my_folios", methods=["GET", "POST"])
def my_folios():
    delete_form = MyFolio()
    folio_id = request.form.get("folio_id")
    session_user_id = session.get("user_id")
    # delete folio form handling
    if delete_form.validate_on_submit():
        # get folio object
        folio = models.Folio.query.get(folio_id)
        # check if folio exists and belongs to user
        if folio and folio.user_id == session_user_id:
            paintings = models.Painting.query.filter_by(folio_id=folio_id)
            for painting in paintings:
                if painting.image:
                    delete_path = f"app/{painting.image}"
                    # delete image from disk
                    if os.path.exists(delete_path):
                        os.remove(delete_path)
                    # remove image path from db
                    painting.image = None
                    db.session.commit()
            # delete paintings
            for painting in paintings:
                db.session.delete(painting)
            # delete panels
            panels = models.Panel.query.filter_by(folio_id=folio_id)
            for panel in panels:
                db.session.delete(panel)
            # delete colour pallete
            colours = models.Bridge.query.filter_by(fid=folio_id)
            for colour in colours:
                db.session.delete(colour)
            # then delete the folio
            db.session.delete(folio)
            db.session.commit()
            flash(f"{folio.theme} folio delete successfully", "success")
            return redirect(url_for("my_folios"))
        else:
            flash("⚠️ Error: Folio not found or access denied", "error")
            return redirect(url_for("my_folios"))
    # check if user logged in
    if not session_user_id:
        flash("⚠️ Please login first", "error")
        return redirect(url_for("login"))
    else:
        folio = models.Folio.query.filter_by(user_id=session_user_id).all()
        # get the first image in the folio to set as thumbnail
        for f in folio:
            first_painting = (
                models.Painting.query.filter_by(folio_id=f.id)
                .filter(models.Painting.image.isnot(None)).first()
            )
            # attach first image attribute to each instances
            # these will the be image paths for the folio thumbnail
            if first_painting:
                f.first_image = first_painting.image
            else:
                f.first_image = None
            print(f.first_image)
        return render_template("my_folios.html",
                               folio=folio,
                               delete_form=delete_form,
                               folio_id=folio_id)


@app.route("/dashboard")
def dashboard():
    session_user_id = session.get("user_id")
    # check if user logged in
    if not session_user_id:
        flash("⚠️ Please login first", "error")
        return redirect(url_for("login"))
    else:
        user_info = models.User.query.get(session['user_id'])
        return render_template("dashboard.html",
                               user_info=user_info,
                               user_id=session_user_id)


@app.route("/edit_folio/<int:folio_id>", methods=['GET', 'POST'])
def edit_folio(folio_id):
    form = ImageUpload()
    delete_form = DeleteImage()
    session_user_id = session.get("user_id")
    painting_id = request.form.get("painting_id")
    folio = models.Folio.query.get_or_404(folio_id)
    # get colour pallete of folio
    colours = (
        models.Colour.query
        .join(models.Bridge, models.Bridge.cid == models.Colour.id)
        .filter(models.Bridge.fid == folio.id).all()
    )
    # check if logged in
    if not session_user_id:
        flash("⚠️ Please log in to edit a folio", "error")
        return redirect(url_for("login"))
    user = db.session.get(models.User, session_user_id)
    if not user:
        flash("⚠️ User not found", "error")
        return redirect(url_for("dashboard"))
    # Verify if that folio belong to the user
    if session_user_id != folio.user_id:
        abort(404)
        return redirect(url_for("dashboard"))
    # check if the form sent is the delete form
    if "delete_image" in request.form and delete_form.validate_on_submit():
        painting = models.Painting.query.get(painting_id)
        # image path to delete
        delete_path = f"app/{painting.image}"
        # delete image if it exists on the disk
        if painting.image and os.path.exists(delete_path):
            os.remove(delete_path)
        # remove image path from the database
        painting.image = None
        db.session.commit()
        flash("Image deleted successfully", "success")
        return redirect(url_for("edit_folio",
                        folio_id=folio_id))
    # handles image upload form
    elif form.validate_on_submit():
        file = request.files['painting_image']
        # see if anything uploaded
        if file.filename == "":
            flash("⚠️ No selected file", "error")
            return redirect(url_for("edit_folio",
                                    folio_id=folio_id))

        # function checking if filetype is valid
        def allowed_file(filename):
            if "." not in filename:
                return False
            # split the file name into two parts between the '.'
            # then get the extension
            file_extension = filename.rsplit('.', 1)[1].lower()
            allowed_extensions = ['png', 'jpg', 'jpeg']
            if file_extension in allowed_extensions:
                return True
            else:
                return False
        # check if file extension is valid
        if file and allowed_file(file.filename):
            # make filename cleaner (no spaces, special chaaracters)
            orginal_filename = secure_filename(file.filename)
            # split filename into two parts for renaming later
            filename_part, extension_part = os.path.splitext(orginal_filename)
            # assign number to filename incase of a double up
            file_number = 1
            while True:
                numbered_filename = f"{filename_part}_{file_number}{extension_part}"
                # check for filename double up
                if os.path.exists(f"app/static/images/{numbered_filename}"):
                    # if yes file number at the end changes to make path unique
                    file_number += 1
                else:
                    break
            save_path = f"app/static/images/{numbered_filename}"
            database_path = f"/static/images/{numbered_filename}"
            file.save(save_path)
            painting = models.Painting.query.get(painting_id)
            # update image path in db
            painting.image = database_path
            db.session.commit()
            flash("Image uploaded successfully", "success")
            return redirect(url_for("edit_folio",
                                    folio_id=folio_id,
                                    ))
        else:
            flash("⚠️ File type not supported", "error")
    # get all paintings and order them in accending position number
    paintings = models.Painting.query.filter_by(folio_id=folio_id).order_by(
        models.Painting.position).all()
    return render_template("edit_folio.html",
                           paintings=paintings,
                           folio=folio,
                           form=form,
                           delete_form=delete_form,
                           colours=colours)


@app.route("/edit_folio/<int:folio_id>/colour", methods=['GET', 'POST'])
def select_colour(folio_id):
    session_user_id = session.get("user_id")
    folio = models.Folio.query.get_or_404(folio_id)
    user = models.User.query.get(session_user_id)
    colours = models.Colour.query.all()
    # check if logged in
    if not session_user_id:
        flash("⚠️ Please log in to edit a folio", "error")
        return redirect(url_for("login"))
    # verify user id
    if not user:
        flash("⚠️ User not found", "error")
        return redirect(url_for("dashboard"))
    # verify folio id
    if not folio:
        flash("⚠️ Folio not found", "error")
        return redirect(url_for("dashboard"))
    # verify if folio belongs to the user
    if session_user_id != folio.user_id:
        abort(404)
    # colour selection handling
    if request.method == 'POST':
        selected_colours = request.form.getlist("select_colour")
        # Validate number of colours selected
        if len(selected_colours) < 2:
            flash("⚠️ Please pick 2 to 4 colours", "error")
            return redirect(url_for('select_colour',
                                    folio_id=folio_id))
        elif len(selected_colours) > 4:
            flash("⚠️ Please pick 2 to 4 colours", "error")
            return redirect(url_for('select_colour',
                                    folio_id=folio_id))
        else:
            # put newly selected colours into database
            # if there are colours already assigned then remove them
            if folio.colour_assignment == 1:
                models.Bridge.query.filter_by(fid=folio.id).delete()
            for i in selected_colours:
                new_colours = models.Bridge(fid=folio.id, cid=i)
                db.session.add(new_colours)
            # update colour assignment column in folio table
            # 0 = no pallete, 1 = pallete assigned
            folio.colour_assignment = 1
            db.session.commit()
            flash("Colour pallete saved", "success")
            return redirect(url_for("edit_folio",
                                    folio_id=folio.id))
    return render_template("select_colour.html",
                           colours=colours,
                           folio=folio,
                           user=user,)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('root'))


@app.route("/help")
def help():
    user_id = session.get("user_id")
    return render_template("help.html",
                           user_logged_in=user_id,
                           user_id=user_id)


# admin pages
@app.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        # checks if the user has entered both a username and password
        if not username or not password:
            flash("⚠️ Please enter a username and a password", "error")
            return redirect(url_for('admin_login'))
        # looks for account in the database
        user = models.User.query.filter_by(name=username).first()
        if not user:
            flash("⚠️ Incorrect name or password", "error")
            return redirect(url_for('admin_login'))
        # get privilege value of the account
        privilege = user.privilege
        # check if username and passwords matches with database
        if user and user.check_password(password):
            # verify admin previlege
            # admin = 1, normal user = 0
            if privilege != 1:
                flash('''⚠️ Something went wrong, please try again''', "error")
                return redirect(url_for("root"))
            else:
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
        session.clear()
        return redirect(url_for("root"))
    return render_template("admin_dashboard.html")


@app.route("/admin/view_users")
def admin_view_users():
    session_admin_id = session.get("admin_id")
    # check if logged in as admin
    if not session_admin_id:
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
        folio = models.Folio.query.get(folio_id)
        # check if folio exists
        if folio:
            # delete image file on disk
            paintings = models.Painting.query.filter_by(folio_id=folio_id)
            for painting in paintings:
                if painting.image:
                    delete_path = f"app/{painting.image}"
                    # check if image path exists
                    if os.path.exists(delete_path):
                        os.remove(delete_path)
                    # remove image path from database
                    painting.image = None
                    db.session.commit()
            # delete all paintings within that folio
            for painting in paintings:
                db.session.delete(painting)
            # delete panels
            panels = models.Panel.query.filter_by(folio_id=folio_id)
            for panel in panels:
                db.session.delete(panel)
            # delete colour pallete of folio
            colours = models.Bridge.query.filter_by(fid=folio_id)
            for colour in colours:
                db.session.delete(colour)
            # then delete the folio
            db.session.delete(folio)
            db.session.commit()
            flash(f"{folio.theme} folio delete successfully", "success")
            return redirect(url_for("admin_view_user_folios",
                                    user_id=user_id,))
        else:
            flash("Error: Folio not found", "error")
            return redirect(url_for("admin_view_user_folios",
                                    user_id=user_id,))
    # check if logged in as admin
    if not session_admin_id:
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
    paintings = models.Painting.query.filter_by(folio_id=folio_id).order_by(
        models.Painting.position).all()
    user = models.User.query.get(user_id)
    colours = (
        models.Colour.query
        .join(models.Bridge, models.Bridge.cid == models.Colour.id)
        .filter(models.Bridge.fid == folio.id).all()
    )
    # check if logged in as admin
    if not session_admin_id:
        session.clear()
        return redirect(url_for("root"))
    # handles image delete
    # admins will not be able to upload images
    if delete_form.validate_on_submit():
        painting = models.Painting.query.get(painting_id)
        # get path to delete
        delete_path = f"app/{painting.image}"
        # check if image exists on disk an in database
        if painting.image and os.path.exists(delete_path):
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
                           user=user,
                           colours=colours)


# error handling
@app.errorhandler(404)
def page_not_found(error):
    user_id = session.get("user_id")
    return render_template("404.html",
                           user_logged_in=user_id,
                           user_id=user_id)


@app.errorhandler(500)
def server_error(error):
    user_id = session.get("user_id")
    return render_template("500.html",
                           user_logged_in=user_id,
                           user_id=user_id), 500
