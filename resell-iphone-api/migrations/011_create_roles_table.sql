-- Создаем таблицу roles
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Вставляем базовые роли
INSERT INTO roles (name, description) VALUES
    ('buyer', 'Покупатель - может просматривать и покупать товары'),
    ('seller', 'Продавец - может создавать и управлять своими товарами'),
    ('admin', 'Администратор - имеет полный доступ к системе');

-- Добавляем внешний ключ в таблицу users
ALTER TABLE users ADD COLUMN role_id INTEGER REFERENCES roles(id);

-- Устанавливаем значение по умолчанию для существующих пользователей
UPDATE users SET role_id = (SELECT id FROM roles WHERE name = 'buyer') WHERE role_id IS NULL;

-- Делаем колонку role_id обязательной
ALTER TABLE users ALTER COLUMN role_id SET NOT NULL;

-- Создаем индекс для оптимизации поиска по ролям
CREATE INDEX idx_users_role_id ON users(role_id); 