from app.routes import db


class Colour(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    hex_code = db.Column(db.String(7), unique=True)