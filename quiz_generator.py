import os


def create_quiz_questions():
    quiz = []
    dirpath = os.path.join(os.getcwd(), 'quiz')
    file = os.path.join(dirpath, '3f15.txt')
    with open(file, 'r', encoding='KOI8-R') as file:
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