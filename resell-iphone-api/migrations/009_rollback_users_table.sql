-- Удаляем существующий первичный ключ
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey;

-- Удаляем существующее ограничение уникальности для telegram_id
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_telegram_id_key;

-- Добавляем колонку id
ALTER TABLE users ADD COLUMN id SERIAL PRIMARY KEY;

-- Добавляем ограничение уникальности для telegram_id
ALTER TABLE users ADD CONSTRAINT users_telegram_id_key UNIQUE (telegram_id);

-- Обновляем внешние ключи в зависимых таблицах
ALTER TABLE items 
    DROP CONSTRAINT IF EXISTS items_user_id_fkey,
    ADD CONSTRAINT items_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(id); 