import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext
)
import database
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    logger.info(
        f"Пользователь {user.username} ({user.id}) запустил бота."
    )

    # Добавляем пользователя в базу данных
    try:
        database.add_user(user.id, user.username, user.first_name)
        welcome_message = (
            f"Привет, {user.first_name}! Отправляй мне свои расходы в "
            "формате:\n\n(сумма) (комментарий)\n\nНапример:\n500 Такси\n\n"
            "Также вы можете отправить дату в формате дд.мм.гггг, чтобы "
            "получить расходы за определённый день."
        )
        await update.message.reply_text(welcome_message)
        logger.info(
            f"Пользователь {user.username} добавлен в базу данных."
        )
    except Exception as e:
        logger.error(
            f"Ошибка при добавлении пользователя {user.id} в базу данных: {e}"
        )
        await update.message.reply_text(
            "Извините, произошла ошибка при добавлении вас в базу данных."
        )

async def add_expense(update: Update, context: CallbackContext) -> None:
    try:
        message_text = update.message.text.strip()
        user_id = update.message.from_user.id

        # Проверяем, что сообщение не пустое
        if not message_text:
            await update.message.reply_text(
                "Пожалуйста, отправьте сообщение в формате:\n"
                "(сумма) (комментарий)\nили дату в формате дд.мм.гггг"
            )
            return

        # Проверяем, является ли сообщение датой в формате дд.мм.гггг
        try:
            date = datetime.strptime(message_text, '%d.%m.%Y').date()
            # Получаем расходы за указанную дату
            await get_expenses_by_date(update, context, date)
            return
        except ValueError:
            # Если не дата, продолжаем обработку как расход
            pass

        # Разделяем сообщение на сумму и комментарий
        parts = message_text.split(maxsplit=1)

        # Проверяем наличие суммы
        if len(parts) == 0:
            await update.message.reply_text(
                "Пожалуйста, укажите сумму расхода.\n"
                "Формат:\n(сумма) (комментарий)"
            )
            return

        amount_text = parts[0]
        description = parts[1] if len(parts) > 1 else None

        # Проверяем, что сумма является числом
        try:
            amount = float(amount_text.replace(',', '.'))
        except ValueError:
            await update.message.reply_text(
                "Некорректная сумма. Пожалуйста, отправьте число в формате:\n"
                "(сумма) (комментарий)\nили дату в формате дд.мм.гггг"
            )
            return

        # Проверяем, что сумма положительная
        if amount <= 0:
            await update.message.reply_text(
                "Сумма должна быть положительным числом."
            )
            return

        logger.info(
            f"Пользователь {user_id} добавил расход: {amount}, "
            f"комментарий: '{description}'"
        )

        # Добавляем расход в базу данных
        database.add_expense(user_id, amount, description)
        response_message = f"Расход в размере {amount} добавлен."
        if description:
            response_message += f" Комментарий: '{description}'."
        await update.message.reply_text(response_message)
        logger.info(
            f"Расход {amount} для пользователя {user_id} успешно записан."
        )
    except Exception as e:
        logger.error(
            f"Ошибка при обработке сообщения от пользователя {user_id}: {e}"
        )
        await update.message.reply_text(
            "Извините, произошла ошибка при обработке вашего сообщения."
        )

async def get_expenses_by_date(update: Update,
                               context: CallbackContext,
                               date):
    user_id = update.message.from_user.id
    try:
        expenses, total_spent = database.get_expenses_by_date(user_id, date)
        if not expenses:
            await update.message.reply_text(
                f"У вас нет расходов за {date.strftime('%d.%m.%Y')}."
            )
            return

        message_lines = [f"Все траты за {date.strftime('%d.%m.%Y')}:"]

        for amount, description in expenses:
            description_text = f" {description}" if description else ""
            message_lines.append(f"{amount}{description_text}")

        message_lines.append(
            f"\nИтого за {date.strftime('%d.%m.%Y')}: {total_spent}"
        )

        await update.message.reply_text('\n'.join(message_lines))
        logger.info(
            f"Пользователь {user_id} запросил расходы за "
            f"{date.strftime('%d.%m.%Y')}."
        )
    except Exception as e:
        logger.error(
            f"Ошибка при получении расходов за дату {date} для пользователя "
            f"{user_id}: {e}"
        )
        await update.message.reply_text(
            "Извините, произошла ошибка при получении ваших расходов."
        )

async def total(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    try:
        expenses, total_spent = database.get_daily_total(user_id)
        logger.info(
            f"Пользователь {user_id} запросил расходы за сегодня."
        )

        if not expenses:
            await update.message.reply_text(
                "У вас нет расходов за сегодня."
            )
            return

        # Формируем сообщение со списком расходов
        message_lines = ["Все траты за сегодня:"]
        for amount, description in expenses:
            description_text = f" {description}" if description else ""
            message_lines.append(f"{amount}{description_text}")

        message_lines.append(f"\nИтого за сегодня: {total_spent}")

        # Отправляем сообщение пользователю
        await update.message.reply_text('\n'.join(message_lines))
        logger.info(
            f"Общие расходы для пользователя {user_id}: {total_spent}"
        )
    except Exception as e:
        logger.error(
            f"Ошибка при получении расходов для пользователя {user_id}: {e}"
        )
        await update.message.reply_text(
            "Извините, произошла ошибка при получении ваших расходов."
        )

def main() -> None:
    logger.info("Бот запущен.")

    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("total", total))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense)
    )

    # Запускаем бота
    logger.info("Бот работает и слушает сообщения.")
    application.run_polling()

if __name__ == '__main__':
    main()
