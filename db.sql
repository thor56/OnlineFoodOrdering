create database OnlineFoodOrdering;
-- Use your database
USE OnlineFoodOrdering;

-- User table (common to all user)
CREATE TABLE User (
    userId INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role ENUM('customer', 'restaurant', 'admin') NOT NULL
);

-- Customers table
CREATE TABLE Customer (
    userId INT,
    address VARCHAR(255) NOT NULL,
    paymentDetails VARCHAR(255),
    FOREIGN KEY (userId) REFERENCES User(userId)
);

-- Admins table
-- CREATE TABLE Admins (
--     userId INT,
--     FOREIGN KEY (userId) REFERENCES User(userId)
-- );

-- Restaurants table
CREATE TABLE Restaurant (
    restaurantId INT ,
    location VARCHAR(255) NOT NULL,
    FOREIGN KEY (restaurantId) REFERENCES User(userId)
);

-- MenuItems table
CREATE TABLE MenuItems (
    itemId INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DOUBLE NOT NULL,
    description TEXT,
    restaurantId INT, 
    FOREIGN KEY (restaurantId) REFERENCES Restaurant(restaurantId)
);

-- Orders table
CREATE TABLE Orders (
    orderId INT AUTO_INCREMENT PRIMARY KEY,
    custId INT,
    restaurantId INT,
    status ENUM('placed', 'confirmed', 'prepared', 'delivered', 'cancelled') NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DOUBLE NOT NULL,
    FOREIGN KEY (custId) REFERENCES Customer(userId),
    FOREIGN KEY (restaurantId) REFERENCES Restaurant(restaurantId)
);

-- OrderItems table (to manage multiple items in a single order)
CREATE TABLE OrderItems (
    orderItemId INT AUTO_INCREMENT PRIMARY KEY,
    orderId INT,
    itemId INT,
    quantity INT NOT NULL,
    FOREIGN KEY (orderId) REFERENCES Orders(orderId),
    FOREIGN KEY (itemId) REFERENCES MenuItems(itemId)
);

-- Payments table
CREATE TABLE Payments (
    transactionId INT AUTO_INCREMENT PRIMARY KEY,
    orderId INT,
    total DOUBLE NOT NULL,
    status ENUM('pending', 'completed', 'refunded') NOT NULL,
    mode ENUM('credit_card', 'debit_card', 'paypal', 'cash') NOT NULL,
    cardDetails VARCHAR(255),
    FOREIGN KEY (orderId) REFERENCES Orders(orderId)
);

-- Reviews table
CREATE TABLE Reviews (
    reviewId INT AUTO_INCREMENT PRIMARY KEY,
    orderId INT,
    content TEXT NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rating DOUBLE NOT NULL CHECK (rating >= 0 AND rating <= 5),
    FOREIGN KEY (orderId) REFERENCES Orders(orderId)
);

-- Carts table
CREATE TABLE Carts (
    cartId INT AUTO_INCREMENT PRIMARY KEY,
    custId INT,
    FOREIGN KEY (custId) REFERENCES Customer(userId)
);

-- CartItems table (to manage multiple items in a single cart)
CREATE TABLE CartItems (
    cartItemId INT AUTO_INCREMENT PRIMARY KEY,
    cartId INT,
    itemId INT,
    quantity INT NOT NULL,
    FOREIGN KEY (cartId) REFERENCES Carts(cartId),
    FOREIGN KEY (itemId) REFERENCES MenuItems(itemId)
);

ALTER TABLE MenuItems ADD COLUMN status ENUM('active', 'deleted') NOT NULL DEFAULT 'active';
	ALTER TABLE User ADD COLUMN reset_code VARCHAR(255);
	ALTER TABLE User ADD COLUMN reset_code_expiry DATETIME;
    ALTER TABLE User ADD CONSTRAINT Unique_person UNIQUE (username,email);
    ALTER TABLE RESTAURANT add column RestaurantName  VARCHAR(100);
    alter table user add column active INT default 1;