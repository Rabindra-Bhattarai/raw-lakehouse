-- Catalog tables: things that exist before anyone buys. Loaded once from the Olist CSVs.
-- MySQL runs every file in this folder, in name order, the first time it starts with an empty volume.
-- /var/lib/mysql-files is the only folder MySQL may load files from (secure-file-priv).

USE shop;

CREATE TABLE sellers (
  seller_id               CHAR(32) PRIMARY KEY,
  seller_zip_code_prefix  CHAR(5),
  seller_city             VARCHAR(100),
  seller_state            CHAR(2)
);

LOAD DATA INFILE '/var/lib/mysql-files/olist_sellers_dataset.csv'
INTO TABLE sellers
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

CREATE TABLE product_category_name_translation (
  product_category_name          VARCHAR(100) PRIMARY KEY,
  product_category_name_english  VARCHAR(100)
);

-- This file was saved on Windows: lines end with \r\n.
LOAD DATA INFILE '/var/lib/mysql-files/product_category_name_translation.csv'
INTO TABLE product_category_name_translation
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES;

-- The source misspells "length" as "lenght"; we fix the names here, and empty cells become NULL.
CREATE TABLE products (
  product_id                  CHAR(32) PRIMARY KEY,
  product_category_name       VARCHAR(100),
  product_name_length         INT,
  product_description_length  INT,
  product_photos_qty          INT,
  product_weight_g            INT,
  product_length_cm           INT,
  product_height_cm           INT,
  product_width_cm            INT
);

LOAD DATA INFILE '/var/lib/mysql-files/olist_products_dataset.csv'
INTO TABLE products
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(product_id, @category, @name_len, @desc_len, @photos, @weight, @length, @height, @width)
SET
  product_category_name      = NULLIF(@category, ''),
  product_name_length        = NULLIF(@name_len, ''),
  product_description_length = NULLIF(@desc_len, ''),
  product_photos_qty         = NULLIF(@photos, ''),
  product_weight_g           = NULLIF(@weight, ''),
  product_length_cm          = NULLIF(@length, ''),
  product_height_cm          = NULLIF(@height, ''),
  product_width_cm           = NULLIF(@width, '');
