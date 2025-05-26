from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length

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
    submit = SubmitField("Submit")