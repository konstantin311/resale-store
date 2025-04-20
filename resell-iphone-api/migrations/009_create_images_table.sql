CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id),
    file_path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add ON DELETE CASCADE to ensure images are deleted when item is deleted
ALTER TABLE images ADD CONSTRAINT fk_item_images 
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE; 