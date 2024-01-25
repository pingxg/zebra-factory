from . import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    """User model
    
    Represents a user with id, email, password and name.
    """
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    name = db.Column(db.String)

class Customer(db.Model):
    """Customer model 
    
    Represents a customer with id, customer name, address, 
    company name, phone number, priority level, and packing type.
    """
    __tablename__ = "salmon_customer"
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String)
    address = db.Column(db.String)
    company = db.Column(db.String)
    phone = db.Column(db.String)
    priority = db.Column(db.Integer)
    packing = db.Column(db.String)
    fish_size = db.Column(db.String)

class Order(db.Model):
    """Order model
    
    Represents an order with id, customer, date, product, 
    price, quantity and weights (relationship to OrderWeight).
    """
    __tablename__ = "salmon_orders"
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String, db.ForeignKey('salmon_customer.customer'))
    date = db.Column(db.Date)
    product = db.Column(db.String)
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    weights = db.relationship('OrderWeight', backref='salmon_order', lazy=True, cascade='all, delete, delete-orphan')
    fish_size = db.Column(db.String)


class OrderWeight(db.Model):
    """OrderWeight model
    
    Represents the weight details of an order with id, order_id (foreign key to Order), 
    quantity, production_time, and batch_number.
    """
    __tablename__ = "salmon_order_weight"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('salmon_orders.id'), nullable=False)
    quantity = db.Column(db.Float)
    production_time = db.Column(db.DateTime)
    batch_number = db.Column(db.Integer)

class ProductName(db.Model):
    """ProductName model
    
    Represents a product name with id, product name, 
    and product type (relationship to Order product).
    """
    __tablename__ = "salmon_product_name"
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String, db.ForeignKey('salmon_orders.product'))
    product_type = db.Column(db.String)

class MaterialInfo(db.Model):
    """MaterialInfo model
    
    Represents the material information of an order with id, farmer, 
    date, and batch_number (foreign key to OrderWeight).
    """
    __tablename__ = "salmon_material_info"
    id = db.Column(db.Integer, primary_key=True)
    farmer = db.Column(db.String)
    date = db.Column(db.Date)
    batch_number = db.Column(db.Integer, db.ForeignKey('salmon_order_weight.batch_number'))