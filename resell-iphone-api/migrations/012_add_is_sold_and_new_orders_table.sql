-- Add is_sold column to items table
ALTER TABLE items ADD COLUMN is_sold BOOLEAN DEFAULT FALSE NOT NULL;

-- Drop existing orders table if exists
DROP TABLE IF EXISTS orders;

-- Create new orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    buyer_id BIGINT NOT NULL REFERENCES users(id),
    seller_id BIGINT NOT NULL REFERENCES users(id),
    item_id INTEGER NOT NULL REFERENCES items(id),
    buyer_telegram_id BIGINT NOT NULL,
    seller_telegram_id BIGINT NOT NULL,
    buyer_phone TEXT NOT NULL,
    seller_phone TEXT NOT NULL,
    delivery_address TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('CREATED', 'PAID')),
    total FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
); 