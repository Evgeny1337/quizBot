import os


def create_quiz_questions(quiz_path):
    quiz = []
    with open(quiz_path, 'r', encoding='KOI8-R') as file:
        content = file.read().split('\n\n')
    question = ''
    for text in content:
        if 'Вопрос' in text:
            question = text.split(":")[1].strip()
        if 'Ответ' in text:
            answer = text.split(":")[1].strip()
            quiz.append((question, answer))
            question = ''
    return quiz