import random
import smtplib
import string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import datetime
from typing import Sequence
from flask import Flask, make_response, redirect, render_template, request, flash, jsonify, session, url_for
from flask_bootstrap import Bootstrap5
 

app = Flask(__name__)
bootstrap = Bootstrap5(app)
app.config['DEBUG'] = True
# $env:FLASK_APP = "app"
# $env:FLASK_ENV = "development"
# $env:FLASK_DEBUG = "1"

# Database configuration with MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@127.0.0.1:3306/onlinefoodordering'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret string'
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
    reset_code = db.Column(db.String(255), nullable=True)
    reset_code_expiry = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Integer)

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
    RestaurantName = db.Column(db.String(255), nullable=False)

# MenuItem Model
class MenuItem(db.Model):
    __tablename__ = 'MenuItems'
    itemId = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    restaurantId = db.Column(db.Integer, db.ForeignKey('Restaurant.restaurantId'))
    status = db.Column(db.Enum('active', 'deleted'), default='active', nullable=False)

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

# USER BASED OPERATIONS

@app.route('/api/users/register', methods=['POST'])
def register_user():
    # data = request.get_json()
    new_user = User(
        username=request.form['username'],
        email=request.form['email'],
        password= request.form['password'],
        role=request.form['role'],
        active = 1
    )

    db.session.add(new_user)
    db.session.flush()  # Flush to get the user ID without committing the transaction

    if(request.form['role'] == 'customer'):
        # Create Customer with the new User ID
        new_customer = Customer(
            userId=new_user.userId,
            address=request.form['address'],
            paymentDetails=request.form['paymentDetails']  
        )
        db.session.add(new_customer)
        # db.session.flush() 
        # cart = Cart()
        # cart.custId = new_customer.userId
        # db.session.add(cart)
        # db.session.flush() 

    elif(request.form['role'] == 'restaurant'):
    # Create Restaurant with the new User ID
        new_restaurant = Restaurant(
            restaurantId=new_user.userId,
            location=request.form['location']
        )
        db.session.add(new_restaurant)

    db.session.commit()
    
    return render_template('login.html', hasError = True,errorMessage = "User registered successfully! Please login")

@app.route("/SignOut")
def SignOut():
    session['userid'] = ''
    session['loggedIn'] = False
    return render_template('login.html', hasError = True,errorMessage = "Logged out!")

@app.route('/api/users/login', methods=['POST'])
def login_user():
    # data = request.form
    user = User.query.filter_by(username=request.form['username']).first()
    
    if not user or user.password != request.form['password']:
        return render_template('login.html', hasError = True,errorMessage = "Invalid login details")
    else:
        print("entered")
        session['userid'] = user.userId
        session['loggedIn'] = True
        session['role'] = user.role
    return render_template('index.html')

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
 
# manage restaurant
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

@app.route('/api/users/<int:user_id>', methods=['GET'])
def delete_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'No user found.'}), 404
    
    # if user.role == 'customer':
    #     cust = Customer.query.get(user_id)
    #     db.session.delete(cust)
    # elif user.role == 'restaurant':
    #     rest_ = Restaurant.query.get(user_id)
    #     db.session.delete(rest_)
    user.active = 0
    # db.session.delete(user)
    db.session.commit()
    return redirect(url_for('SignOut',method='GET'))

# CUSTOMER BASED OPERATIONS
@app.route('/api/restaurants', methods=['GET'])
def view_restaurants():
    restaurants = Restaurant.query.filter_by().all()
    res_lis = []
    for r in restaurants:
        user = User.query.get(r.restaurantId)
        r_details = {
            'id' : r.restaurantId,
            'name' : user.username,
            'location' : r.location
        }
        if(user.active == 1):
            res_lis.append(r_details)
    return res_lis

# view menu
@app.route('/api/restaurants/<int:restaurant_id>/menu', methods=['GET'])
def view_menu(restaurant_id):
    menu_items = MenuItem.query.filter_by(restaurantId=restaurant_id, status='active').all()
    cart_items = {}
    ext_restaurant_id = None
    has_cart = False
    

    if 'loggedIn' in session and session['loggedIn'] == True :
        user_id = session['userid']
        cart_ = Cart.query.filter_by(custId = user_id).first()
        if cart_ is not None:
            cart_id = cart_.cartId
            if cart_id is not None:
                has_cart = True
                temp_id = 0
                cart_items_2 = CartItem.query.filter_by(cartId = cart_id).all()
                if cart_items_2 is not None:
                    for item in cart_items_2:
                        cart_items[item.itemId] = item
                        temp_id = item.itemId
                    m_item = MenuItem.query.filter_by(itemId = temp_id).first()
                    if m_item is not None:
                        ext_restaurant_id = m_item.restaurantId
    if ext_restaurant_id is not None:
        same_rest = restaurant_id == ext_restaurant_id
    else :
        same_rest = True
    if(not type(cart_items) == type({})):
        cart_items = {}
    return render_template('viewMenu.html', menu = menu_items, cart_items = cart_items, has_cart = has_cart, same_rest = same_rest)




@app.route('/api/customers/<int:customerId>/<int:itemId>/<int:qty>/cart', methods=['GET'])
def add_item_to_cart(customerId, itemId, qty):
    # data = request.get_json()
    cart = Cart.query.filter_by(custId = customerId).first()
    if(cart is None):
        cart = Cart()
        cart.custId = customerId
        db.session.add(cart)
        db.session.flush() 
    cart_item = CartItem.query.filter_by(itemId = itemId, cartId = cart.cartId).first()
    if(cart_item is None):
        cart_item = CartItem()
        cart_item.cartId = cart.cartId
        cart_item.itemId = itemId
        cart_item.quantity = 1
    else :
        
        if qty == 0:
            qty = -1
        cart_item.quantity = cart_item.quantity + qty
        if(cart_item.quantity == 0):
            db.session.delete(cart_item)
            db.session.commit()
            return make_response('', 204)
    
    current_item = MenuItem.query.get(itemId)
    if not current_item:
        return make_response('Item not found', 404)

    current_restaurant_id = current_item.restaurantId
    # Check if there are items in the cart from a different restaurant
    cart_items = CartItem.query.join(MenuItem).filter(
        CartItem.cartId == cart.cartId,
        MenuItem.restaurantId != current_restaurant_id
    ).all()

    if cart_items:
        # Remove all items from a different restaurant
        for item in cart_items:
            db.session.delete(item)


    db.session.add(cart_item)
    db.session.commit()
    return make_response('', 204)

# view cart
@app.route('/api/customers/cart', methods=['GET'])
def view_cart():
    cart = Cart.query.filter_by(custId=session['userid']).first()
    items_details = []
    total = 0
    if cart:
        cart_items = CartItem.query.filter_by(cartId=cart.cartId).all()
        
        
        for item in cart_items:
            menu_item = MenuItem.query.get(item.itemId)
            if menu_item:
                total += menu_item.price * item.quantity
                item_detail = {
                    'itemId': item.itemId,
                    'name': menu_item.name,
                    'price': menu_item.price,
                    'description': menu_item.description,
                    'quantity': item.quantity
                }
                items_details.append(item_detail)

    return render_template('viewCart.html', cartContents = items_details, cart_total = total, custId=session['userid'])

# update cart
@app.route('/api/customers/<int:customerId>/cart/items/<int:itemId>', methods=['PUT'])
def update_cart_item(customerId, itemId):
    data = request.get_json()
    cart = Cart.query.filter_by(custId=customerId).first()
    if not cart:
        return jsonify({'message': 'Cart not found'}), 404

    cart_item = CartItem.query.filter_by(cartId=cart.cartId, itemId=itemId).first()
    if cart_item:
        cart_item.quantity = data['quantity']
        db.session.commit()
        return jsonify({'message': 'Cart item updated'}), 200
    else:
        return jsonify({'message': 'Cart item not found'}), 404

# delete cart item
@app.route('/api/customers/<int:customerId>/cart/items/<int:itemId>', methods=['DELETE'])
def delete_cart_item(customerId, itemId):
    cust_cart = Cart.query.filter_by(custId=customerId).first()
    cart_item = CartItem.query.filter_by(cartId=cust_cart.cartId, itemId=itemId).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'message': 'Cart item deleted'}), 200
    return jsonify({'message': 'Cart item not found'}), 404

# checkout
@app.route('/api/customers/<int:customerId>/checkout', methods=['GET'])
def checkout(customerId):
    # Fetch cart details first
    cart_details = Cart.query.filter_by(custId = customerId).first()
    customer_details = Customer.query.filter_by(userId= customerId).first()
    # Fetch cart items
    cart_items = CartItem.query.filter_by(cartId=cart_details.cartId).all()
    if not cart_items:
        return jsonify({'message': 'Cart is empty'}), 400

    # Create an order
    new_order = Order(custId=customerId, status='placed', total=0 )  # Calculate total based on cart items
    db.session.add(new_order)
    db.session.flush()  # Flush to get the order ID without committing the transaction

    # Move items from cart to order and calculate total
    total = 0
    for item in cart_items:
        order_item = OrderItem(orderId=new_order.orderId, itemId=item.itemId, quantity=item.quantity)
        db.session.add(order_item)
        menu_item = MenuItem.query.filter_by(itemId=item.itemId).first()
        new_order.restaurantId = menu_item.restaurantId
        total += menu_item.price * item.quantity  # Assuming item has a price attribute

    new_order.total = total

    # Record the payment
    payment = Payment(orderId=new_order.orderId, total=total, status='completed', mode='credit_card', cardDetails = customer_details.paymentDetails)
    db.session.add(payment)

    # Clear the cart
    for item in cart_items:
        db.session.delete(item)
    db.session.delete(cart_details)
    db.session.commit()
    return redirect(url_for('view_orders'))

# # view orders
# @app.route('/api/customers/<int:customerId>/orders', methods=['GET'])
# def view_orders(customerId):
#     orders = Order.query.filter_by(custId=customerId).all()
#     orders_details = [{'orderId': order.orderId, 'restaurant_id' : order.restaurantId, 'status': order.status, 'total': order.total, 'Date' : order.date} for order in orders]
#     return jsonify(orders_details), 200

@app.route('/api/customers/orders', methods=['GET'])
def view_orders():
    order_details = []
    customerId = session['userid']
    orders = Order.query.filter_by(custId=customerId).all()
    for order in orders:
        rest_id = order.restaurantId
        rest_details = Restaurant.query.filter_by(restaurantId = rest_id).first()
        o_detail = {
            'orderId': order.orderId,
            'restaurantName': rest_details.RestaurantName,  # Assuming 'name' is a field in User model
            'restaurantLocation': rest_details.location,  # Assuming 'location' is a field in User model
            'status': order.status,
            'total': order.total,
            'Date': order.date
        }
        order_details.append(o_detail)
    
    return render_template('viewOrders.html', orders = order_details)



# manage order - update order status
@app.route('/api/orders/', methods=['POST'])
def update_order_status():
    data =  request.get_json() 
    orderId = int(data['orderId'])
    status = data['status']

    order = Order.query.get(orderId)
    if not order:
        return jsonify({'message': 'Order not found.'}), 404
        
    order.status = status
    db.session.commit()
    return  jsonify({'message': 'Order status updated successfully.'}), 200


# rendering review page
@app.route("/review/<int:orderId>")
def ReviewPage(orderId):
       # Check if a review already exists for this order
    old_rev = False
    existing_review = Review.query.filter_by(orderId=orderId).first()
    if existing_review:
        old_rev = True
    return render_template('addReview.html', orderId = orderId, old_rev = old_rev)

# add review
@app.route('/api/orders/<int:orderId>/review', methods=['POST'])
def review_order(orderId):
    data = request.get_json()
    # Check if the order exists
    order = Order.query.get(orderId)
    if not order:
        return jsonify({'message': 'Order not found.'}), 404
    
    # Create a new review
    new_review = Review(
        orderId=orderId,
        content=data['content'],
        rating=data['rating']
    )
    db.session.add(new_review)
    db.session.commit()

    request.method = 'GET'
    return redirect(url_for('view_orders'))

# manage review
@app.route('/api/reviews/<int:orderId>', methods=['PUT', 'DELETE'])
def manage_review(orderId):
    review = Review.query.filter_by(orderId = orderId).first()

    if not review:
        return jsonify({'message': 'Review not found.'}), 404

    if request.method == 'PUT':
        data = request.get_json()
        review.content = data.get('content', review.content)
        review.rating = data.get('rating', review.rating)
        db.session.commit()
        message = 'Review upadted successfully'

    elif request.method == 'DELETE':
        db.session.delete(review)
        db.session.commit()
        message = 'review deleted successfully'

    return redirect(url_for('view_orders'))

# manage customer profile
@app.route('/api/customers/<int:customerId>/profile', methods=['PUT', 'DELETE'])
def manage_customer_profile(customerId):
    customer = Customer.query.get(customerId)
    user = User.query.get(customer.userId) if customer else None

    if not customer or not user:
        return jsonify({'message': 'Customer not found.'}), 404

    if request.method == 'PUT':
        data = request.get_json()
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        customer.address = data.get('address', customer.address)
        customer.paymentDetails = data.get('paymentDetails', customer.paymentDetails)
        db.session.commit()
        return jsonify({'message': 'Customer profile updated successfully.'}), 200

    elif request.method == 'DELETE':
        db.session.delete(customer)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'Customer profile deleted successfully.'}), 200

# RESTAURANT BASED OPERAITONS

# rendering login page
@app.route("/updateMenu/<int:itemId>")
def updateMenu(itemId):
    return render_template('updateMenu.html',itemId = itemId )

@app.route("/addMenu")
def addMenu():
    return render_template('addMenu.html' )

# add menu item
@app.route('/api/restaurants/menu', methods=['POST'])
def add_menu_item():
    data = request.get_json()
    # new_item = MenuItem()
    # new_item.name = data['name']
    # new_item.price = data['price']
    # new_item.description = data['description']
    # new_item.restaurantId = session['userid']
    new_item = MenuItem(
        name=data['name'],
        price=data['price'],
        description=data['description'],
        restaurantId = session['userid']
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'message': 'Menu item added successfully', 'itemId': new_item.itemId}), 201

# manage Menu
@app.route('/api/menuitems/<int:itemId>', methods=['PUT', 'DELETE'])
def manage_menu_item(itemId):
    menu_item = MenuItem.query.get(itemId)

    if not menu_item:
        return jsonify({'message': 'Menu item not found.'}), 404

    if request.method == 'PUT':
        data = request.get_json()
        menu_item.name = data.get('name', menu_item.name)
        menu_item.price = data.get('price', menu_item.price)
        menu_item.description = data.get('description', menu_item.description)
        db.session.commit()
        return jsonify({'message': 'Menu item updated successfully.'}), 200

    elif request.method == 'DELETE':
        menu_item = MenuItem.query.get(itemId)
        if menu_item:
            menu_item.status = 'deleted'
            db.session.commit()
            return jsonify({'message': 'Menu item marked as deleted'}), 200
        else:
            return jsonify({'message': 'Menu item not found'}), 404

# delete menu
@app.route('/deleteMenu/<int:itemId>', methods=['GET'])
def delete_menu_item(itemId):
    menu_item = MenuItem.query.get(itemId)
    if menu_item:
        menu_item.status = 'deleted'
        db.session.commit()
        return jsonify({'message': 'Menu item marked as deleted'}), 200
    else:
        return jsonify({'message': 'Menu item not found'}), 404

# view orders - for restaurant
@app.route('/api/restaurants/<int:restaurantId>/orders', methods=['GET'])
def view_received_orders(restaurantId):
    orders = Order.query.filter(
        Order.restaurantId == restaurantId, 
        Order.status != 'delivered'
    ).order_by(Order.date.asc()).all()

    order_details = [{
        'orderId': order.orderId, 
        'customerId': order.custId, 
        'status': order.status, 
        'date': order.date
    } for order in orders]

    return jsonify(order_details), 200

# ADMIN BASED OPERATIONS
# view users
@app.route('/api/admin/users', methods=['GET'])
def view_all_users():
    users = User.query.all()
    user_details = []

    for user in users:
        user_info = {
            'userId': user.userId,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }

        
        user_details.append(user_info)

    return render_template('viewUsers.html', users=user_details)


@app.route('/user-profile/<int:userId>')
def user_profile(userId):
    user_id  = userId
    user = User.query.get(user_id)
    if not user:
        return 'User not found', 404

    profile_data = None
    if user.role == 'customer':
        profile_data = Customer.query.filter_by(userId=user_id).first()
    elif user.role == 'restaurant':
        profile_data = Restaurant.query.filter_by(restaurantId=user_id).first()

    return render_template('userProfile.html', user=user, profile_data=profile_data)

@app.route('/update-user-profile/<int:user_id>')
def update_user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return 'User not found', 404

    # Ensure the current user is authorized to update this profile
    # ...

    if user.role == 'customer':
        customer = Customer.query.filter_by(userId=user_id).first()
        return render_template('updateUserProfile.html', user=user, customer=customer)
    elif user.role == 'restaurant':
        restaurant = Restaurant.query.filter_by(restaurantId=user_id).first()
        return render_template('updateUserProfile.html', user=user, restaurant=restaurant)
    else:
        # Handle other user roles or errors
        return 'Invalid user role', 400




@app.route('/submit-user-update/<int:user_id>', methods=['POST'])
def submit_user_update(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('home'))

    # Update common user fields
    user.username = request.form['username']
    user.email = request.form['email']
    user.password = request.form['password']
    # Include additional common fields if any

    if user.role == 'customer':
        # Assuming you have a one-to-one relationship between User and Customer
        customer = Customer.query.filter_by(userId=user_id).first()
        if customer:
            customer.address = request.form['address']
            customer.paymentDetails = request.form.get('paymentDetails')  # Optional field
            # Include additional customer-specific fields if any
        else:
            flash('Customer profile not found', 'error')
            return redirect(url_for('home'))

    elif user.role == 'restaurant':
        # Assuming you have a one-to-one relationship between User and Restaurant
        restaurant = Restaurant.query.filter_by(restaurantId=user_id).first()
        if restaurant:
            restaurant.location = request.form['location']
            # Include additional restaurant-specific fields if any
        else:
            flash('Restaurant profile not found', 'error')
            return redirect(url_for('home'))

    # Save the changes
    db.session.commit()
    flash('Profile updated successfully', 'success')
    return redirect(url_for('user_profile', userId=user_id))



# Forgot password
@app.route('/api/users/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user:
        # Generate a random reset code
        reset_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        user.reset_code = reset_code
        user.reset_code_expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        db.session.commit()

        # Logic to send email to user's email address
        send_reset_email(user.email, reset_code)

        return jsonify({'message': 'If the email is registered, a reset code has been sent.'}), 200
    return jsonify({'message': 'If the email is registered, a reset code has been sent.'}), 200

def send_reset_email(email, code):
    sender_email = "your_email@example.com"
    receiver_email = email
    password = "your_email_password"  # Consider using environment variables for sensitive data

    message = f"""\
    Subject: Password Reset Code

    Your password reset code is {code}."""

    try:
        server = smtplib.SMTP('smtp.example.com', 587)  # Use your SMTP server details
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
    except Exception as e:
        return jsonify({'message': 'Failed to send email.', 'error': str(e)}), 500

    return jsonify({'message': 'Password reset code sent to your email.'}), 200

@app.route('/api/users/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    user = User.query.filter_by(reset_code=data['reset_code']).first()
    if user and user.reset_code_expiry > datetime.datetime.utcnow():
        # Hash new password and reset the reset_code fields
        hashed_password = data['new_password']
        user.password = hashed_password
        user.reset_code = None
        user.reset_code_expiry = None
        db.session.commit()
        return jsonify({'message': 'Password has been reset successfully.'}), 200
    return jsonify({'message': 'Invalid or expired reset code.'}), 400


@app.route('/restaurant-orders/<int:restaurant_id>')
def restaurant_orders(restaurant_id):
    orders = Order.query.filter_by(restaurantId=restaurant_id).all()

    return render_template('restaurantOrders.html', orders=orders, restaurant_id=restaurant_id)

@app.route('/manageOrder/<int:orderId>', methods=['POST','GET'])
def viewManageRestaurant(orderId):
    order = Order.query.filter_by(orderId = orderId).first()
    return render_template('manageOrder.html', order=order)


# FRONTEND ------------------ APPLICATIONS

@app.route("/")
def home():
    if session.__contains__("loggedIn") == False:
        session['userid'] = ''
        session['loggedIn'] = False
    restaurants = view_restaurants()
    return render_template('index.html', restaurants = restaurants)

# rendering login page
@app.route("/login")
def LoginPage():
    return render_template('login.html', hasError = False)

# sign up page
@app.route("/register")
def SignUpPage():
    return render_template('signup.html')





if __name__ == '__main__':
    app.run(debug=True)
