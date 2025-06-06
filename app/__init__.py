from flask import Flask, session
app = Flask(__name__)
from app import routes
app.run(debug=True)

import secrets
# Creates a random key that is 64 characters long to encrypt session data
# This makes more secure and protects against seesion hijacking 
app.secret_key = secrets.token_hex(32)

# makes a function that injects the user_id of the logged in user
# so that all templates can excess
@app.context_processor
def add_session_user():
    #get the user_id form the session, if they are logged in
    user_id = session.get("user_id")
    # returns as a dictionary so that its avaible for all jinja templates 
    return dict(user_id=user_id)

