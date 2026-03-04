-- PERHAPS have better check for names and not just that the cant be empty strings
-- PERHAPS some delete cascade things. (ON DELETE CASCADE)
-- PERHAPS change from date so we have both date and time
-- ADD DATE TO ORDER

DO $$ BEGIN
    CREATE TYPE diet_type AS ENUM ('carnivore', 'omnivore', 'herbivore');
EXCEPTION 
    WHEN duplicate_object THEN NULL; 
END $$;

DO $$ BEGIN
    CREATE TYPE region_type AS ENUM ('south africa', 'america', 'asia', 'north america', 'europe', 'south america', 'africa');
EXCEPTION 
    WHEN duplicate_object THEN NULL; 
END $$;

DO $$ BEGIN
    CREATE TYPE dino_type_type AS ENUM ('terrestrial');
EXCEPTION 
    WHEN duplicate_object THEN NULL; 
END $$;
    
CREATE TABLE IF NOT EXISTS users (
    name VARCHAR(50) NOT NULL CHECK(name <> ''), 
    user_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    email VARCHAR(50) UNIQUE NOT NULL CHECK(email <> ''),
    password VARCHAR(255) NOT NULL CHECK(password <> ''),
    admin BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    product_name VARCHAR(50) NOT NULL CHECK(product_name <> ''),
    weight INTEGER,
    height DECIMAL(10, 2),
    length DECIMAL(10, 2),
    diet diet_type,
    region region_type,
    dino_type dino_type_type,
    description TEXT,
    image TEXT,
    stock INTEGER NOT NULL,
    amount_sold INTEGER NOT NULL DEFAULT 0,
    price INTEGER,
    published BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id INTEGER NOT NULL, 
    order_complete BOOLEAN NOT NULL DEFAULT FALSE,
    order_date DATE DEFAULT CURRENT_DATE,
    shipped_date DATE,
 
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id INTEGER NOT NULL,
    product_name VARCHAR(50) NOT NULL CHECK(product_name <> ''),
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    list_price INTEGER,

    PRIMARY KEY (order_id, product_id),

    FOREIGN KEY (order_id) REFERENCES orders (order_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id)
);

CREATE TABLE IF NOT EXISTS cart (
    cart_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id INTEGER NOT NULL UNIQUE, 
 
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS cart_items (
    cart_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),

    PRIMARY KEY (cart_id, product_id),

    FOREIGN KEY (cart_id) REFERENCES cart (cart_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id)
);

CREATE TABLE IF NOT EXISTS review (
    review_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    product_id INTEGER NOT NULL,
    review_text TEXT,
    grade INTEGER CHECK(grade >= 1 AND grade <= 5) NOT NULL,
    user_id INTEGER NOT NULL,
    verified_customer BOOLEAN,
    date DATE DEFAULT CURRENT_DATE,

    UNIQUE (product_id, user_id),

    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id)
);