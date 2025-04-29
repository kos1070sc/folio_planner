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
    privilege = db.Column(db.Integer, default=0)  # 0 is normal user, 1 is admin

def set_password(self, password):
    self.password = generate_password_hash(password, method='pbkdf2:sha256', salt_length = 8)
    #This function hashes the password before storing it
    #It uses PBKDF2-SHA256 password hasher with 8 byte salt 
    #This means that the hashed password will always be 60 characters long

def check_password(self, password):
    return check_password_hash(self.password, password)
    #This compares the password to the stored hash to check if a password is correct
    #If it mathes it will return True if not then False 

