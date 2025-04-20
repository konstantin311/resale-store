-- Add is_sold column to items table
ALTER TABLE items ADD COLUMN is_sold BOOLEAN DEFAULT FALSE NOT NULL; 