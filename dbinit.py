from flask import current_app

INIT_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS Store (
    id int NOT NULL AUTO_INCREMENT,
    store_name varchar(50) NOT NULL,
    address varchar(255) NOT NULL,
    name varchar(50) NOT NULL,
    phone varchar(20) NOT NULL,
    photo varchar(255) DEFAULT 'store.jpg',
    priority int DEFAULT 0,
    password varchar(120) NOT NULL,
    PRIMARY KEY (id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS Product (
    product_id int NOT NULL AUTO_INCREMENT,
    store_id int NOT NULL,
    product_name varchar(50) NOT NULL,
    material_type varchar(20) NOT NULL,
    price int NOT NULL,
    color varchar(20) NOT NULL,
    changing_date datetime NOT NULL,
    photo varchar(255) DEFAULT 'product.jpg',
    PRIMARY KEY (product_id),
    FOREIGN KEY (store_id) REFERENCES Store(id) ON UPDATE CASCADE ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS Customer (
    id int NOT NULL AUTO_INCREMENT,
    fav_store_id int,
    name varchar(50) NOT NULL,
    phone varchar(20) NOT NULL,
    password varchar(120) NOT NULL,
    photo varchar(255) DEFAULT 'default.jpg',
    register_date date NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (fav_store_id) REFERENCES Store(id) ON DELETE SET NULL ON UPDATE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS Orders (
    order_id int NOT NULL AUTO_INCREMENT,
    customer_id int NOT NULL,
    order_date date NOT NULL,
    PRIMARY KEY (order_id),
    FOREIGN KEY (customer_id) REFERENCES Customer(id) ON UPDATE CASCADE ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS OrderDetails (
    details_id int NOT NULL AUTO_INCREMENT,
    order_id int NOT NULL,
    product_id int NOT NULL,
    product_quantity int NOT NULL,
    total_price int NOT NULL,
    PRIMARY KEY (details_id),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON UPDATE CASCADE ON DELETE CASCADE
    );
    """
]
 