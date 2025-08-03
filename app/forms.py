from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_wtf.file import FileField

#form for login
class LoginForm(FlaskForm):
    #username field
    username = StringField('Username', validators=[
        #makes username a required field 
        DataRequired(message = "⚠️ Please enter a username"), 
        #sets the max and min length 
        Length(min = 3, max = 30, message = "⚠️ Enter a username between 3 - 30 characters please")
        ]) 
    
    #password field
    password = PasswordField("Password", validators=[
        #makes password a required field 
        DataRequired(message = "⚠️ Please enter a password"), 
        #sets the min length of password 
        Length(min = 8, message = "⚠️ Please enter a password of at least 8 characters please")
        ]) 
    submit = SubmitField("Login")

#form for create account
class CreateAccount(FlaskForm):
    #username field
    username = StringField('Username', validators=[
        #makes username a required field 
        DataRequired(message = "⚠️ Please enter a username"), 
        #sets the max and min length 
        Length(min = 3, max = 30, message = "⚠️ Enter a username between 3 - 30 characters please")
        ]) 
    
    #password field
    password = PasswordField("Password", validators=[
        #makes password a required field 
        DataRequired(message = "⚠️ Please enter a password"), 
        #sets the min length of password 
        Length(min = 8, message = "⚠️ Please enter a password of at least 8 characters please")
        ]) 
    
    confirm_password = PasswordField("CofirmPassword", validators=[
        #makes password a required field 
        DataRequired(message = "⚠️ Please enter a password"), 
        # check if the same as password
        EqualTo('password', message="⚠️ Password must match")
        ]) 
    submit = SubmitField("Create Account")


# Create New Theme
class CreateNew(FlaskForm):
    theme = StringField('Theme', validators=[
        DataRequired(message = "⚠️ Please enter a theme"),
        Length(max=50, message = "⚠️ Please enter a theme with less than 50 characters")
    ])
    submit = SubmitField("Submit")

#Upload Image
class ImageUpload(FlaskForm):
    painting_image = FileField("Painting Image")
    submit = SubmitField('Submit')

# Delelte Image
class DeleteImage(FlaskForm):
    delete_image = SubmitField("Delete Image")

# Delete Folio
class MyFolio(FlaskForm):
    delete_folio = SubmitField("Delete")