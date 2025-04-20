-- Сначала удаляем внешние ключи в зависимых таблицах
ALTER TABLE phones DROP CONSTRAINT IF EXISTS phones_user_id_fkey;
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_user_id_fkey;
ALTER TABLE items DROP CONSTRAINT IF EXISTS items_user_id_fkey;

-- Удаляем существующий первичный ключ в таблице users с CASCADE
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey CASCADE;

-- Удаляем существующее ограничение уникальности для telegram_id
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_telegram_id_key;

-- Делаем telegram_id первичным ключом
ALTER TABLE users ADD PRIMARY KEY (telegram_id);

-- Обновляем внешние ключи в зависимых таблицах
ALTER TABLE phones 
    ALTER COLUMN user_id TYPE BIGINT,
    ADD CONSTRAINT phones_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(telegram_id);

ALTER TABLE orders 
    ALTER COLUMN user_id TYPE BIGINT,
    ADD CONSTRAINT orders_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(telegram_id);

ALTER TABLE items 
    ALTER COLUMN user_id TYPE BIGINT,
    ADD CONSTRAINT items_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(telegram_id); 