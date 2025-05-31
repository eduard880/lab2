import MySQLdb

try:
    conn = MySQLdb.connect(
        host='localhost',
        user='root',
        passwd='edik2005',
        db='bookstore'
    )
    print("Успешное подключение к MySQL!")
    conn.close()
except MySQLdb.Error as e:
    print(f"Ошибка подключения: {e}")