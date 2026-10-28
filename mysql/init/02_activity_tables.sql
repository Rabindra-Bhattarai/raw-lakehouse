-- Activity tables for MySQL
-- things that happen over time. The replay script fills them


CREATE TABLE customers (
    customer_id CHAR(32) PRIMARY KEY,
    customer_unique_id CHAR(32) NOT NULL,
    customer_zip_code_prefix CHAR(5),
    customer_city VARCHAR(50),
    customer_state CHAR(2)
);

CREATE TABLE orders (
    order_id CHAR(32) PRIMARY KEY,
    customer_id CHAR(32) NOT NULL,
    order_status VARCHAR(20) NOT NULL,
    order_purchase_timestamp DATETIME NOT NULL,
    order_approved_at DATETIME,
    order_delivered_carrier_date DATETIME,
    order_delivered_customer_date DATETIME,
    order_estimated_delivery_date DATETIME,
    updated_at TIMESTAMP(3)
    DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)
);

CREATE TABLE order_items (
    order_id CHAR(32) NOT NULL,
    order_item_id INT NOT NULL,
    product_id CHAR(32) NOT NULL,
    seller_id CHAR(32) NOT NULL,
    shipping_limit_date DATETIME,
    price DECIMAL(10,2) NOT NULL,
    freight_value DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE order_payments (
    order_id CHAR(32) NOT NULL,
    payment_sequential INT NOT NULL,
    payment_type VARCHAR(20),
    payment_installments INT,
    payment_value DECIMAL(10,2),
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE TABLE order_reviews (
    review_id CHAR(32) NOT NULL,
    order_id CHAR(32) NOT NULL,
    review_score TINYINT,
    review_comment_title VARCHAR(255),
    review_comment_message TEXT,
    review_creation_date DATETIME,
    review_answer_timestamp DATETIME,
    updated_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY(review_id, order_id)
);





