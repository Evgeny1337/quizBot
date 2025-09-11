import os

import redis
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from quiz_generator import create_quiz_questions

QUESTION, ANSWER = range(2)

def get_keyboard():
    custom_keyboard = [['Новый вопрос','Сдаться'],['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    return reply_markup

def start_handler(update: Update, context: CallbackContext):
    update.message.reply_text('Здравствуйте', reply_markup=get_keyboard())
    return QUESTION

def handle_new_question_request(update: Update, context: CallbackContext):
    quiz = context.bot_data['quiz']
    redis_connect = context.bot_data['redis_connect']
    user_id = int(update.message.from_user.id)
    if redis_connect.exists(user_id):
        question_number = int(redis_connect.get(user_id))
        if question_number + 1 >= len(quiz):
            update.message.reply_text('Вопросы закончились')
        else:
            question = quiz[question_number + 1][0]
            redis_connect.set(user_id, question_number + 1)
            update.message.reply_text(question)
    else:
        question = quiz[0][0]
        redis_connect.set(user_id, 0)
        update.message.reply_text(question)

    return ANSWER

def handle_solution_attempt(update: Update, context: CallbackContext):
    user_answer = update.message.text
    redis_connect = context.bot_data['redis_connect']
    quiz = context.bot_data['quiz']
    user_id = update.message.from_user.id
    question_number = redis_connect.get(user_id)
    answer = quiz[question_number][1]
    if user_answer == answer:
        update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос')
        return QUESTION
    else:
        update.message.reply_text('Неправильно… Попробуешь ещё раз?')
        return ANSWER


def handle_get_score(update: Update, context: CallbackContext):
    update.message.reply_text('Сколько-то очков')

def handle_give_up(update: Update, context: CallbackContext):
    redis_connect = context.bot_data['redis_connect']
    quiz = context.bot_data['quiz']
    user_id = int(update.message.from_user.id)
    question_number = int(redis_connect.get(user_id))
    answer = quiz[question_number][1]
    next_question = quiz[question_number + 1][0]
    redis_connect.set(user_id, question_number + 1)
    update.message.reply_text(answer)
    update.message.reply_text(next_question)
    return QUESTION

def main():
    load_dotenv()
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.flushall()
    tg_token = os.getenv('TG_TOKEN')
    updater = Updater(tg_token, use_context=True)
    quiz = create_quiz_questions()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_handler)],

        states={
            QUESTION: [MessageHandler(Filters.regex(r'^Новый вопрос'), handle_new_question_request),
                       MessageHandler(Filters.regex(r'Сдаться'), handle_give_up)],

            ANSWER: [MessageHandler(Filters.regex(r'Сдаться'), handle_give_up)
                    ,MessageHandler(Filters.text, handle_solution_attempt)]
        },

        fallbacks=[CommandHandler('give_up', handle_give_up)],

        per_message=False,
        allow_reentry=True,
    )
    dispatcher = updater.dispatcher
    dispatcher.add_handler(conv_handler)
    dispatcher.bot_data['redis_connect'] = r
    dispatcher.bot_data['quiz'] = quiz

    updater.start_polling()


if __name__ == '__main__':
    main()