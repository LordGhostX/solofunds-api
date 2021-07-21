from datetime import datetime
from solofunds import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String, primary_key=True, nullable=False)
    verification_level = db.Column(db.Integer, nullable=False, default=0)
    date_created = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)

    basic_info = db.relationship(
        "VerificationBasicInfo", backref="users", lazy=True)
    verification_doc = db.relationship(
        "VerificationDocument", backref="users", lazy=True)
    verification_image = db.relationship(
        "VerificationImage", backref="users", lazy=True)


class VerificationBasicInfo(db.Model):
    __tablename__ = "basic_info"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    ssn = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    dob = db.Column(db.DateTime, nullable=False)


class VerificationDocument(db.Model):
    __tablename__ = "verification_doc"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    document_type = db.Column(db.String, nullable=False)
    document_base64 = db.Column(db.String, nullable=False)
    face_image = db.Column(db.String, nullable=False)


class VerificationImage(db.Model):
    __tablename__ = "verification_image"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    picture_base64 = db.Column(db.String, nullable=False)
