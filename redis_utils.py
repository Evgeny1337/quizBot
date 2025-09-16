import json
import random


def get_good_score(redis_connect, user_id, bot_type):
    redis_user_good_answer = 'user_{}_{}_good_answer'.format(bot_type, user_id)
    if redis_connect.exists(redis_user_good_answer):
        score = redis_connect.get(redis_user_good_answer)
        return {
            'redis_user_good_answer': redis_user_good_answer,
            'score': score}
    redis_connect.set(redis_user_good_answer, 0)
    return {'redis_user_good_answer': redis_user_good_answer, 'score': 0}


def get_bad_score(redis_connect, user_id, bot_type):
    redis_user_bad_answer = 'user_{}_{}_bad_answer'.format(bot_type, user_id)
    if redis_connect.exists(redis_user_bad_answer):
        score = redis_connect.get(redis_user_bad_answer)
        return {'redis_user_bad_answer': redis_user_bad_answer, 'score': score}
    redis_connect.set(redis_user_bad_answer, 0)
    return {'redis_user_bad_answer': redis_user_bad_answer, 'score': 0}


def get_new_question(redis_connect, user_id, bot_type):
    redis_user_id = 'user_{}_{}'.format(bot_type, user_id)

    question_count = int(redis_connect.get('question_count'))
    new_question_number = random.randint(0, question_count)
    redis_question_number = 'question_{}'.format(new_question_number)

    new_question = json.loads(redis_connect.get(redis_question_number))
    new_redis_question = json.dumps(
        {'last_asked_question': redis_question_number})
    redis_connect.set(redis_user_id, new_redis_question)

    return new_question


def check_answer(redis_connect, user_id, answer, bot_type):
    redis_user_id = 'user_{}_{}'.format(bot_type, user_id)
    redis_last_asked_question = json.loads(redis_connect.get(redis_user_id))
    last_asked_question = redis_last_asked_question['last_asked_question']

    if answer and last_asked_question == answer:
        redis_good_score = get_good_score(redis_connect, user_id, bot_type)
        redis_user_good_answer = redis_good_score['redis_user_good_answer']
        score = redis_good_score['score']
        redis_connect.set(redis_user_good_answer, score)
        return True
    else:
        redis_bad_score = get_bad_score(redis_connect, user_id, bot_type)
        redis_user_bad_answer = redis_bad_score['redis_user_bad_answer']
        score = redis_bad_score['score']
        redis_connect.set(redis_user_bad_answer, score)
        return False


def check_score(redis_connect, user_id, bot_type):
    redis_user_good_answer = get_good_score(redis_connect, user_id, bot_type)
    redis_user_bad_answer = get_bad_score(redis_connect, user_id, bot_type)
    return {'redis_user_good_answer': redis_user_good_answer,
            'redis_user_bad_answer': redis_user_bad_answer}


def get_last_question_info(redis_connect, user_id, bot_type):
    redis_user_id = 'user_{}_{}'.format(bot_type, user_id)
    redis_last_asked_question = json.loads(redis_connect.get(redis_user_id))
    last_asked_question = redis_last_asked_question['last_asked_question']
    redis_question = json.loads(redis_connect.get(last_asked_question))
    return redis_question


def report_question(redis_connect, user_id, bot_type):
    redis_user_id = 'user_{}_{}'.format(bot_type, user_id)
    user_data = json.loads(redis_connect.get(redis_user_id))
    question_key = user_data['last_asked_question']

    reports_key = 'reported_questions'
    current_reports = json.loads(redis_connect.get(reports_key) or '{}')

    if question_key not in current_reports:
        current_reports[question_key] = []

    if user_id not in current_reports[question_key]:
        current_reports[question_key].append(user_id)

    redis_connect.set(reports_key, json.dumps(current_reports))
