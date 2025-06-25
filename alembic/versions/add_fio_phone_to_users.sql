-- Добавить поля fio и phone в таблицу users

ALTER TABLE users
    ADD COLUMN fio VARCHAR(128),
    ADD COLUMN phone VARCHAR(20);
