from flask import Flask, session
app = Flask(__name__)
from app import routes
app.run(debug=False)

import secrets
# encrypt session data
app.secret_key = secrets.token_hex(32)


@app.context_processor
def add_session_user():
    # get the user_id form the session, if they are logged in
    user_id = session.get("user_id")
    # returns as a dictionary so that its avaible for all jinja templates
    return dict(user_id=user_id)
