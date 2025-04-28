from app.routes import db
from werkzeug.security import generate_password_hash, check_password_hash

class Colour(db.Model):
    __tablename__ = "Colour"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    hex_code = db.Column(db.String(7), unique=True)

class User(db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    privilege = db.Column(db.Integer, default=0)  # 0 is normal user 1 is admin
