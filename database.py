import psycopg2
import logging
from datetime import date


# Настройка логирования
logger = logging.getLogger(__name__)

# Функция для подключения к базе данных
def get_connection():
    try:
        conn = psycopg2.connect(
            dbname="expenses_db",
            user="postgres",
            password="1",
            host="localhost",
            port="5433"
        )
        logger.info("Соединение с базой данных установлено.")
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        raise

# Добавление нового пользователя в базу данных
def add_user(user_id, username, first_name):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (user_id, username, first_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING
            """,
            (user_id, username, first_name)
        )
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Пользователь {user_id} ({username}) добавлен в базу данных.")
    except Exception as e:
        logger.error(f"Ошибка при добавлении пользователя {user_id} в базу данных: {e}")
        raise

# Добавление расхода с комментарием
def add_expense(user_id, amount, description=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO expenses (user_id, amount, description)
            VALUES (%s, %s, %s)
            """,
            (user_id, amount, description)
        )
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Расход {amount} для пользователя {user_id} добавлен с описанием: '{description}'.")
    except Exception as e:
        logger.error(f"Ошибка при добавлении расхода для пользователя {user_id}: {e}")
        raise

# Получение списка расходов и общей суммы за день
def get_daily_total(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT amount, description
            FROM expenses
            WHERE user_id = %s AND DATE(timestamp) = CURRENT_DATE
            ORDER BY timestamp
            """,
            (user_id,)
        )
        expenses = cursor.fetchall()
        total = sum(expense[0] for expense in expenses) if expenses else 0
        cursor.close()
        conn.close()
        return expenses, total
    except Exception as e:
        logger.error(f"Ошибка при получении расходов для пользователя {user_id}: {e}")
        raise
    
def get_expenses_by_date(user_id, target_date):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT amount, description
            FROM expenses
            WHERE user_id = %s AND DATE(timestamp) = %s
            ORDER BY timestamp
            """,
            (user_id, target_date)
        )
        expenses = cursor.fetchall()
        total = sum(expense[0] for expense in expenses) if expenses else 0
        cursor.close()
        conn.close()
        return expenses, total
    except Exception as e:
        logger.error(f"Ошибка при получении расходов за дату {target_date} для пользователя {user_id}: {e}")
        raise