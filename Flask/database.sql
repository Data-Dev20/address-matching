CREATE DATABASE address_db;

USE address_db;

CREATE TABLE addresses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    address TEXT,
    pincode VARCHAR(10),
    cluster_id INT NULL,
    latitude FLOAT NULL,
    longitude FLOAT NULL
);
