import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CallbackContext, Updater, MessageHandler, Filters, CommandHandler


def main():
    quiz = {}
    dirpath = os.path.join(os.getcwd(), 'quiz')
    file = os.path.join(dirpath, '3f15.txt')
    with open(file, 'r', encoding='KOI8-R') as file:
        content = file.read().split('\n\n')
    question = ''
    for text in content:
        if 'Вопрос' in text:
            question = text
        if 'Ответ' in text:
            quiz[question] = text
            question = ''

    print(quiz)



if __name__ == '__main__':
    main()
