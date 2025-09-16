import logging
import telegram


class TelegramLogsHandler(logging.Handler):
    def __init__(self, chat_id: str, bot: telegram.Bot, level=logging.INFO):
        super().__init__(level)
        self.bot = bot
        self.chat_id = chat_id
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.setFormatter(formatter)

    def emit(self, record):
        log_entry = self.format(record)
        try:
            self.bot.send_message(chat_id=self.chat_id, text=log_entry)
        except Exception as e:
            print(f"Не удалось отправить лог в Telegram: {e}")


def setup_logging(tg_token, log_chat_id):
    logging_bot = telegram.Bot(token=tg_token)

    tg_handler = TelegramLogsHandler(log_chat_id, logging_bot)
    tg_handler.setLevel(logging.ERROR)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    tg_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(tg_handler)
    logger.addHandler(console_handler)

    return logger
