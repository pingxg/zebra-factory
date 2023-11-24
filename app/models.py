from . import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    name = db.Column(db.String)

class Customer(db.Model):
    __tablename__ = "salmon_customer"
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String)
    address = db.Column(db.String)
    company = db.Column(db.String)
    phone = db.Column(db.String)
    priority = db.Column(db.Integer)
    packing = db.Column(db.String)

class SalmonOrder(db.Model):
    __tablename__ = "salmon_orders"
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String, db.ForeignKey('salmon_customer.customer'))
    date = db.Column(db.Date)
    product = db.Column(db.String)
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    
    weights = db.relationship('SalmonOrderWeight', backref='salmon_order', lazy=True, cascade='all, delete, delete-orphan')

class SalmonOrderWeight(db.Model):
    __tablename__ = "salmon_order_weight"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('salmon_orders.id'), nullable=False)
    quantity = db.Column(db.Float)
    production_time = db.Column(db.DateTime)

