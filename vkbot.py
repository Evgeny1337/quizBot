import os
import redis
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from quiz_generator import create_quiz_questions
from dotenv import load_dotenv

def get_keyboard():
    keyboard = VkKeyboard(inline=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def handle_start(vk, user_id, r, keyboard):
    r.set(f'state_{user_id}', 'QUESTION')
    r.delete(f'question_index_{user_id}')
    vk.messages.send(user_id=user_id, message='Здравствуйте', keyboard=keyboard, random_id=0)

def handle_new_question(vk, user_id, r, quiz, keyboard):
    question_index = int(r.get(f'question_index_{user_id}') or 0)
    if question_index >= len(quiz):
        vk.messages.send(user_id=user_id, message='Вопросы закончились', keyboard=keyboard, random_id=0)
        return
    question = quiz[question_index][0]
    r.set(f'question_index_{user_id}', question_index)
    r.set(f'state_{user_id}', 'ANSWER')
    vk.messages.send(user_id=user_id, message=question, keyboard=keyboard, random_id=0)

def handle_give_up(vk, user_id, r, quiz, keyboard):
    question_index = int(r.get(f'question_index_{user_id}') or 0)
    if question_index >= len(quiz):
        return
    answer = quiz[question_index][1]
    next_index = question_index + 1
    r.set(f'question_index_{user_id}', next_index)
    r.set(f'state_{user_id}', 'QUESTION')
    next_question = quiz[next_index][0] if next_index < len(quiz) else 'Вопросы закончились'
    vk.messages.send(user_id=user_id, message=f'{answer}\n\n{next_question}', keyboard=keyboard, random_id=0)

def handle_score(vk, user_id, keyboard):
    vk.messages.send(user_id=user_id, message='Сколько-то очков', keyboard=keyboard, random_id=0)

def handle_answer(vk, user_id, r, quiz, text, keyboard):
    question_index = int(r.get(f'question_index_{user_id}') or 0)
    correct_answer = quiz[question_index][1]
    if text == correct_answer:
        r.set(f'state_{user_id}', 'QUESTION')
        vk.messages.send(user_id=user_id, message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»', keyboard=keyboard, random_id=0)
    else:
        vk.messages.send(user_id=user_id, message='Неправильно… Попробуешь ещё раз?', keyboard=keyboard, random_id=0)

def main():
    load_dotenv(override=True)
    vk_token = os.getenv('VK_TOKEN')
    vk_session = VkApi(token=vk_token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    quiz = create_quiz_questions()

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            text = event.text.strip()
            state = r.get(f'state_{user_id}')
            keyboard = get_keyboard()

            if text == '/start':
                handle_start(vk, user_id, r, keyboard)
            elif text == 'Новый вопрос':
                handle_new_question(vk, user_id, r, quiz, keyboard)
            elif text == 'Сдаться':
                handle_give_up(vk, user_id, r, quiz, keyboard)
            elif text == 'Мой счет':
                handle_score(vk, user_id, keyboard)
            elif state == 'ANSWER':
                handle_answer(vk, user_id, r, quiz, text, keyboard)

if __name__ == '__main__':
    main()