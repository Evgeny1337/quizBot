import json
import os

def create_quiz_questions(quiz_path, redis_client):
    quiz = redis_client.pipeline()
    quiz_files = os.listdir(quiz_path)
    question_index = 0
    for file_name in quiz_files:
        quiz_file_path = os.path.join(quiz_path, file_name)
        with open(quiz_file_path, 'r', encoding='KOI8-R') as file:
            content = file.read().split('\n\n')
            question = ''
            for text in content:
                if 'Вопрос' in text:
                    question = text.split(":")[1].strip()
                if 'Ответ' in text and question:
                    answer = text.split(":")[1].strip().rstrip('.')
                    redis_question_json = json.dumps({"question": question, "answer": answer})
                    quiz.set("question_{}".format(question_index), redis_question_json)
                    question = ''
                    question_index += 1
    quiz.set('question_count',question_index)
    quiz.execute()