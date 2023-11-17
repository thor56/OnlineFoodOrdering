from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
# from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['DEBUG'] = True
# $env:FLASK_APP = "app"
# $env:FLASK_ENV = "development"

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
    __tablename__ = 'Restaurant'
    restaurantId = db.Column(db.Integer, db.ForeignKey('User.userId'), primary_key=True)
    location = db.Column(db.String(255), nullable=False)

# MenuItem Model
class MenuItem(db.Model):
    __tablename__ = 'MenuItems'
    itemId = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    restaurantId = db.Column(db.Integer, db.ForeignKey('Restaurant.restaurantId'))

# Order Model
class Order(db.Model):
    __tablename__ = 'Orders'
    orderId = db.Column(db.Integer, primary_key=True)
    custId = db.Column(db.Integer, db.ForeignKey('Customer.userId'))
    restaurantId = db.Column(db.Integer, db.ForeignKey('Restaurant.restaurantId'))
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
    # hashed_password = generate_password_hash(data['password'], method='sha256')
    
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        role=data['role']
    )

    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully.'}), 201

@app.route('/api/customers', methods=['POST'])
def create_customer():
    data = request.get_json()

    # Create User
    # hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        role='customer'  
    )
    db.session.add(new_user)
    db.session.flush()  # Flush to get the user ID without committing the transaction

    # Create Customer with the new User ID
    new_customer = Customer(
        userId=new_user.userId,
        address=data['address'],
        paymentDetails=data['paymentDetails']  
    )
    db.session.add(new_customer)
    db.session.commit()

    return jsonify({'message': 'New customer created successfully.'}), 201

@app.route('/api/restaurants', methods=['POST'])
def create_restaurant():
    data = request.get_json()

    # Create User
    # hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        role='restaurant'  
    )
    db.session.add(new_user)
    db.session.flush()  

    # Create Restaurant with the new User ID
    new_restaurant = Restaurant(
        restaurantId=new_user.userId,
        location=data['location']
    )
    db.session.add(new_restaurant)
    db.session.commit()

    return jsonify({'message': 'New restaurant created successfully.'}), 201

@app.route('/api/users/login', methods=['POST'])
def login_user():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or user.password != data['password']:
        return jsonify({'message': 'Invalid username or password.'}), 401
    
    return jsonify({'message': 'Login successful.'}), 200

@app.route('/api/customers/<int:user_id>', methods=['PUT'])
def update_customer(user_id):
    data = request.get_json()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'message': 'User not found.'}), 404

    # Update User details
    user.username = data['username']
    user.email = data['email']
    user.password = data['password']
    

    # Update Customer details
    customer = Customer.query.get(user_id)
    if customer:
        customer.address = data['address']
        customer.paymentDetails = data['paymentDetails']  

    db.session.commit()
    return jsonify({'message': 'Customer updated successfully.'}), 200

@app.route('/api/restaurants/<int:user_id>', methods=['PUT'])
def update_restaurant(user_id):
    data = request.get_json()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'message': 'User not found.'}), 404

    # Update User details
    user.username = data['username']
    user.email = data['email']
    user.password = data['password']

    # Update Restaurant details
    restaurant = Restaurant.query.get(user_id)
    if restaurant:
        restaurant.location = data['location']

    db.session.commit()
    return jsonify({'message': 'Restaurant updated successfully.'}), 200



@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'No user found.'}), 404
    
    if user.role == 'customer':
        cust = Customer.query.get(user_id)
        db.session.delete(cust)
    elif user.role == 'restaurant':
        rest_ = Restaurant.query.get(user_id)
        db.session.delete(rest_)

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully.'}), 200

# CUSTOMER BASED OPERATIONS
@app.route('/api/restaurants', methods=['GET'])
def view_restaurants():
    restaurants = Restaurant.query.all()
    res_lis = []
    for r in restaurants:
        user = User.query.get(r.restaurantId)
        r_details = {
            'id' : r.restaurantId,
            'name' : user.username,
            'location' : r.location
        }
        res_lis.append(r_details)
    return jsonify(res_lis)

@app.route('/api/restaurants/<int:restaurant_id>/menu', methods=['GET'])
def view_menu(restaurant_id):
    menu_items = MenuItem.query.filter_by(restaurantId=restaurant_id).all()
    return jsonify([{'itemId': item.itemId, 'name': item.name, 'price': item.price, 'description' : item.description} for item in menu_items])

@app.route('/api/customers/<int:customerId>/cart', methods=['POST'])
def add_item_to_cart(customerId):
    data = request.get_json()
    cart = Cart()
    cart.custId = customerId
    db.session.add(cart)
    db.session.flush() 
    cart_item = CartItem()
    cart_item.cartId = cart.cartId
    cart_item.itemId = data['itemId']
    cart_item.quantity = data['quantity']
    db.session.add(cart_item)
    db.session.commit()
    return jsonify({'message': 'Item added to cart'}), 201


if __name__ == '__main__':
    app.run(debug=True)
