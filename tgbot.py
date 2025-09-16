import os
import redis
import logging
from dotenv import load_dotenv
from logger import setup_logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from quiz_generator import create_quiz_questions
from redis_utils import get_new_question, check_answer, check_score, get_last_question_info, report_question

logger = logging.getLogger(__name__)

QUESTION, ANSWER = range(2)


def get_keyboard():
    custom_keyboard = [['Новый вопрос', 'Сдаться'], [
        'Мой счет'], ['Неверно составленный вопрос']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    return reply_markup


def start_handler(update: Update, context: CallbackContext):
    try:
        update.message.reply_text(
            'Здравствуйте, для того чтобы начать игру, нажмите кнопку Новый вопрос',
            reply_markup=get_keyboard())
        return QUESTION
    except Exception:
        logger.exception("Ошибка в start_handler")
        raise


def handle_new_question_request(update: Update, context: CallbackContext):
    try:
        redis_connect = context.bot_data['redis_connect']
        user_id = int(update.message.from_user.id)
        new_question = get_new_question(redis_connect, user_id, 'tg')
        question = new_question['question']
        update.message.reply_text(question)
        return ANSWER
    except Exception:
        logger.exception("Ошибка в handle_new_question_request")
        raise


def handle_solution_attempt(update: Update, context: CallbackContext):
    try:
        user_answer = update.message.text
        redis_connect = context.bot_data['redis_connect']
        user_id = int(update.message.from_user.id)
        answer_result = check_answer(redis_connect, user_id, user_answer, 'tg')

        if answer_result:
            update.message.reply_text(
                'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос')
            return QUESTION
        else:
            update.message.reply_text(
                'Неправильно… Попробуешь ещё раз?')
            return ANSWER
    except Exception:
        logger.exception("Ошибка в handle_solution_attempt")
        raise


def handle_get_score(update: Update, context: CallbackContext):
    try:
        redis_connect = context.bot_data['redis_connect']
        user_id = int(update.message.from_user.id)
        score_result = check_score(redis_connect, user_id, 'tg')
        good_score = score_result['redis_user_good_answer']
        bad_score = score_result['redis_user_bad_answer']

        answer = 'Количество правильных ответов: {}\n\nКоличество неверных ответов: {}\n\n'.format(
            good_score['score'], bad_score['score'])
        update.message.reply_text(answer)
        update.message.reply_text(
            'Игра закончена, введите команду /start, чтобы начать')
        return ConversationHandler.END
    except Exception:
        logger.exception("Ошибка в handle_get_score")
        raise


def handle_give_up(update: Update, context: CallbackContext):
    try:
        redis_connect = context.bot_data['redis_connect']
        user_id = int(update.message.from_user.id)
        redis_question = get_last_question_info(redis_connect, user_id, 'tg')
        answer = redis_question['answer']
        update.message.reply_text(
            "Ответ на предыдущий вопрос: {}".format(answer))
        check_answer(redis_connect, user_id, False)
        update.message.reply_text('Для продолжения игры нажмите Новый вопрос')
        update.message.reply_text(
            "Если вопрос был составлен некорректно, нажмите 'Неверно составленный вопрос'")
        return QUESTION
    except Exception:
        logger.exception("Ошибка в handle_give_up")
        raise


def handle_report_question(update: Update, context: CallbackContext):
    try:
        redis_connect = context.bot_data['redis_connect']
        user_id = int(update.message.from_user.id)
        update.message.reply_text('На данный вопрос оставлена заявка')
        report_question(redis_connect, user_id, 'tg')
        new_question = get_new_question(redis_connect, user_id, 'tg')
        question = new_question['question']
        update.message.reply_text(
            "Новый вопрос: {}".format(question))
        return ANSWER
    except Exception:
        logger.exception("Ошибка в handle_report_question")
        raise


def main():
    try:
        load_dotenv()
        tg_token = os.getenv('TG_TOKEN')
        tg_logs_token = os.getenv('TG_LOGS_TOKEN')
        log_chat_id = os.getenv('TG_LOG_CHAT_ID')
        setup_logging(tg_logs_token, log_chat_id)

        logger.info("Запуск Telegram бота викторины...")

        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True)
        redis_client.flushall()

        quiz_path = os.getenv('QUIZ_PATH')
        create_quiz_questions(quiz_path, redis_client)

        updater = Updater(tg_token, use_context=True)
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start_handler)],
            states={
                QUESTION: [
                    MessageHandler(
                        Filters.regex(r'^Новый вопрос'),
                        handle_new_question_request),
                    MessageHandler(
                        Filters.regex(r'^Неверно составленный вопрос'),
                        handle_report_question),
                ],
                ANSWER: [
                    MessageHandler(
                        Filters.regex(r'^Мой счет'),
                        handle_get_score),
                    MessageHandler(Filters.regex(r'^Сдаться'), handle_give_up),
                    MessageHandler(Filters.text, handle_solution_attempt),
                ],
            },
            fallbacks=[CommandHandler('give_up', handle_give_up)],
            per_message=False,
            allow_reentry=True,
        )

        dispatcher = updater.dispatcher
        dispatcher.add_handler(conv_handler)
        dispatcher.bot_data['redis_connect'] = redis_client

        updater.start_polling()
        logger.info("Telegram бот викторины запущен успешно")

    except Exception:
        logger.exception("Критическая ошибка при запуске бота")
        raise


if __name__ == '__main__':
    main()
