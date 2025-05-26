import sqlite3

# Пути к базам данных
source_db = 'old_db.sqlite3'
target_db = 'db.sqlite3'

# Подключение к старой (source) базе данных
source_conn = sqlite3.connect(source_db)
source_cursor = source_conn.cursor()

# Подключение к новой (target) базе данных
target_conn = sqlite3.connect(target_db)
target_cursor = target_conn.cursor()

# Чтение всех записей из таблицы kitvariant
source_cursor.execute('''
    SELECT uid, created_at, updated_at, name, price_modifier, "order", image, is_option, code
    FROM products_kitvariant
''')
rows = source_cursor.fetchall()

# Вставка данных в целевую таблицу
for row in rows:
    target_cursor.execute('''
        INSERT OR IGNORE INTO products_kitvariant (
            uid, created_at, updated_at, name, price_modifier, "order", image, is_option, code
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', row)

# Завершаем транзакцию
target_conn.commit()

# Закрываем соединения
source_conn.close()
target_conn.close()

print("✅ Перенос типов комплектаций завершен успешно!")
