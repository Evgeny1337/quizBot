import os
import redis
import logging
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from logger import setup_logging
from quiz_generator import create_quiz_questions
from dotenv import load_dotenv
from redis_utils import get_new_question, check_answer, check_score, get_last_question_info, report_question

logger = logging.getLogger(__name__)


def get_keyboard():
    keyboard = VkKeyboard(inline=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button(
        'Неверно составленный вопрос',
        color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def handle_start(vk, user_id, redis_connect, keyboard):
    try:
        redis_connect.set(f'state_{user_id}', 'QUESTION')
        vk.messages.send(
            user_id=user_id,
            message='Здравствуйте, для того чтобы начать игру, нажмите кнопку Новый вопрос',
            keyboard=keyboard,
            random_id=0)
    except Exception:
        logger.exception("Ошибка в handle_start")
        raise


def handle_new_question(vk, user_id, redis_connect, keyboard):
    try:
        new_question = get_new_question(redis_connect, user_id, 'vk')
        redis_connect.set(f'state_{user_id}', 'ANSWER')
        vk.messages.send(
            user_id=user_id,
            message=new_question['question'],
            keyboard=keyboard,
            random_id=0)
    except Exception:
        logger.exception("Ошибка в handle_new_question")
        raise


def handle_give_up(vk, user_id, redis_connect, keyboard):
    try:
        redis_question = get_last_question_info(redis_connect, user_id, 'vk')
        answer = redis_question['answer']
        check_answer(redis_connect, user_id, False, 'vk')
        vk.messages.send(
            user_id=user_id,
            message=f"Ответ на предыдущий вопрос: {answer}",
            keyboard=keyboard,
            random_id=0)
        vk.messages.send(
            user_id=user_id,
            message="Если вопрос составлен некорректно, нажмите 'Неверно составленный вопрос'",
            keyboard=keyboard,
            random_id=0)
    except Exception:
        logger.exception("Ошибка в handle_give_up")
        raise


def handle_score(vk, user_id, redis_connect, keyboard):
    try:
        score_result = check_score(redis_connect, user_id, 'vk')
        good_score = score_result['redis_user_good_answer']
        bad_score = score_result['redis_user_bad_answer']
        message = f'Количество правильных ответов: {good_score["score"]}\n\nКоличество неверных ответов: {bad_score["score"]}'
        vk.messages.send(
            user_id=user_id,
            message=message,
            keyboard=keyboard,
            random_id=0)
    except Exception:
        logger.exception("Ошибка в handle_score")
        raise


def handle_answer(vk, user_id, redis_connect, text, keyboard):
    try:
        answer_result = check_answer(redis_connect, user_id, text, 'vk')
        if answer_result:
            redis_connect.set(f'state_{user_id}', 'QUESTION')
            vk.messages.send(
                user_id=user_id,
                message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
                keyboard=keyboard,
                random_id=0)
        else:
            vk.messages.send(
                user_id=user_id,
                message='Неправильно… Попробуешь ещё раз?',
                keyboard=keyboard,
                random_id=0)
    except Exception:
        logger.exception("Ошибка в handle_answer")
        raise


def handle_report_question(vk, user_id, redis_connect, keyboard):
    try:
        report_question(redis_connect, user_id, 'vk')
        new_question = get_new_question(redis_connect, user_id, 'vk')
        vk.messages.send(
            user_id=user_id,
            message='На данный вопрос оставлена заявка',
            keyboard=keyboard,
            random_id=0)
        vk.messages.send(
            user_id=user_id,
            message=f"Новый вопрос: {new_question['question']}",
            keyboard=keyboard,
            random_id=0)
    except Exception:
        logger.exception("Ошибка в handle_report_question")
        raise


def main():
    try:
        load_dotenv(override=True)
        vk_token = os.getenv('VK_TOKEN')
        quiz_path = os.getenv('QUIZ_PATH')
        tg_logs_token = os.getenv('TG_LOGS_TOKEN')
        log_chat_id = os.getenv('TG_LOG_CHAT_ID')
        setup_logging(tg_logs_token, log_chat_id)
        vk_session = VkApi(token=vk_token)
        vk = vk_session.get_api()
        longpoll = VkLongPoll(vk_session)
        redis_connect = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True)
        redis_connect.flushall()
        create_quiz_questions(quiz_path, redis_connect)

        for event in longpoll.listen():
            if event.type != VkEventType.MESSAGE_NEW or not event.to_me:
                continue

            user_id = event.user_id
            text = event.text.strip()
            state = redis_connect.get(f'state_{user_id}')
            keyboard = get_keyboard()

            command_handlers = {
                '/start': lambda: handle_start(
                    vk,
                    user_id,
                    redis_connect,
                    keyboard),
                'Новый вопрос': lambda: handle_new_question(
                    vk,
                    user_id,
                    redis_connect,
                    keyboard),
                'Сдаться': lambda: handle_give_up(
                    vk,
                    user_id,
                    redis_connect,
                    keyboard),
                'Мой счет': lambda: handle_score(
                    vk,
                    user_id,
                    redis_connect,
                    keyboard),
                'Неверно составленный вопрос': lambda: handle_report_question(
                    vk,
                    user_id,
                    redis_connect,
                    keyboard)}

            handler = command_handlers.get(text)
            if handler:
                handler()
            elif state == 'ANSWER':
                handle_answer(vk, user_id, redis_connect, text, keyboard)

    except Exception:
        logger.exception("Критическая ошибка при запуске бота")
        raise


if __name__ == '__main__':
    main()
