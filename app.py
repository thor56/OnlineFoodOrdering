from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['DEBUG'] = True

# Database configuration with MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@127.0.0.1:3306/onlinefoodordering'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the Flask app
db = SQLAlchemy(app)

# Define models
class User(db.Model):
    __tablename__ = 'User'
    userId = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)  
    email = db.Column(db.String(255), unique=True, nullable=False)
    role = db.Column(db.Enum('customer', 'restaurant', 'admin'), nullable=False)

# Customer Model
class Customer(db.Model):
    __tablename__ = 'Customer'
    userId = db.Column(db.Integer, db.ForeignKey('User.userId'), primary_key=True)
    address = db.Column(db.String(255), nullable=False)
    paymentDetails = db.Column(db.String(255))  # Secure storage should be considered

# Restaurant Model
class Restaurant(db.Model):
    __tablename__ = 'Restaurants'
    userId = db.Column(db.Integer, db.ForeignKey('User.userId'), primary_key=True)
    location = db.Column(db.String(255), nullable=False)

# MenuItem Model
class MenuItem(db.Model):
    __tablename__ = 'MenuItems'
    itemId = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    restaurantId = db.Column(db.Integer, db.ForeignKey('User.userId'))

# Order Model
class Order(db.Model):
    __tablename__ = 'Orders'
    orderId = db.Column(db.Integer, primary_key=True)
    custId = db.Column(db.Integer, db.ForeignKey('Customer.userId'))
    restaurantId = db.Column(db.Integer, db.ForeignKey('Restaurants.userId'))
    status = db.Column(db.Enum('placed', 'confirmed', 'prepared', 'delivered', 'cancelled'), nullable=False)
    date = db.Column(db.DateTime, default=func.now())
    total = db.Column(db.Float, nullable=False)

# OrderItem Model (to represent each item within an order)
class OrderItem(db.Model):
    __tablename__ = 'OrderItems'
    orderItemId = db.Column(db.Integer, primary_key=True)
    orderId = db.Column(db.Integer, db.ForeignKey('Orders.orderId'))
    itemId = db.Column(db.Integer, db.ForeignKey('MenuItems.itemId'))
    quantity = db.Column(db.Integer, nullable=False)

# Payment Model
class Payment(db.Model):
    __tablename__ = 'Payments'
    transactionId = db.Column(db.Integer, primary_key=True)
    orderId = db.Column(db.Integer, db.ForeignKey('Orders.orderId'))
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum('pending', 'completed', 'refunded'), nullable=False)
    mode = db.Column(db.Enum('credit_card', 'debit_card', 'paypal', 'cash'), nullable=False)
    cardDetails = db.Column(db.String(255))  # Secure storage should be considered

# Review Model
class Review(db.Model):
    __tablename__ = 'Reviews'
    reviewId = db.Column(db.Integer, primary_key=True)
    orderId = db.Column(db.Integer, db.ForeignKey('Orders.orderId'))
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=func.now())
    rating = db.Column(db.Float, nullable=False)

# Cart Model
class Cart(db.Model):
    __tablename__ = 'Carts'
    cartId = db.Column(db.Integer, primary_key=True)
    custId = db.Column(db.Integer, db.ForeignKey('Customer.userId'))

# CartItem Model (to represent each item within a cart)
class CartItem(db.Model):
    __tablename__ = 'CartItems'
    cartItemId = db.Column(db.Integer, primary_key=True)
    cartId = db.Column(db.Integer, db.ForeignKey('Carts.cartId'))
    itemId = db.Column(db.Integer, db.ForeignKey('MenuItems.itemId'))
    quantity = db.Column(db.Integer, nullable=False)

# Establishing relationships
User.customer = db.relationship('Customer', backref='user', uselist=False)
User.restaurants = db.relationship('Restaurant', backref='user')
Restaurant.menu_items = db.relationship('MenuItem', backref='restaurant')
Customer.orders = db.relationship('Order', backref='customer')
Order.order_items = db.relationship('OrderItem', backref='order')
Order.payments = db.relationship('Payment', backref='order')
Order.reviews = db.relationship('Review', backref='order')
Cart.cart_items = db.relationship('CartItem', backref='cart')

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return 'Welcome to the Online Food Ordering System API!'


# USER BASED OPERATIONS

@app.route('/api/users/register', methods=['POST'])
def register_user():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        role=data['role']
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully.'}), 201

@app.route('/api/users/login', methods=['POST'])
def login_user():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid username or password.'}), 401
    
    return jsonify({'message': 'Login successful.'}), 200

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'No user found.'}), 404
    
    user.email = data['email']
    user.username = data['username']
    # You may want to update the password too (remember to hash it)
    
    db.session.commit()
    return jsonify({'message': 'User updated successfully.'}), 200

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'No user found.'}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully.'}), 200




if __name__ == '__main__':
    app.run(debug=True)
