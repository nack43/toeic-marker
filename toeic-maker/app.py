from flask import Flask, render_template, request, g, session, redirect, url_for, abort
import os
import sqlite3
import bcrypt
from datetime import datetime
import sys

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE = '/tmp/toeic-maker.db'

# initialize database from schema.sql (sql_script)
#@app.route('/create_db')
def init_db():
    conn = sqlite3.connect(DATABASE)
    # open db schema file
    with app.open_resource('schema.sql', 'r') as f:
        conn.cursor().executescript(f.read())
    conn.commit()
    conn.close()


def connect_db():
    rv = sqlite3.connect(DATABASE)
    rv.row_factory = sqlite3.Row

    return rv


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()

    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/users/sign_up', methods=['GET', 'POST'])
def sign_up():
    print(sys._getframe().f_code.co_name)
    if request.method == 'GET':
        return render_template('sign_up.html')

    elif request.method == 'POST':
        try:
            db = get_db()

            user = db.cursor().execute('SELECT email_address FROM user WHERE email_address=?', (request.form['email_address'],))

            if user is not None:
                # password hashing
                hashed_pass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())

                # registering new user
                db.cursor().execute("INSERT INTO user(email_address, password) VALUES (?, ?)", 
                    (
                        request.form['email_address'],
                        hashed_pass
                    ))

                db.commit()
                db.close()
                return 'User create successfully'

            else:
                print('THE MAIL ADDRESS ALREADY EXSISTS')
                db.close()
                return 'User create failed'

        except sqlite3.Error as e:
            print(e) # エラー
            db.close()


@app.route('/users/sign_in', methods=['GET', 'POST'])
def sign_in():
    print(sys._getframe().f_code.co_name)
    if request.method == 'GET':
        return render_template('sign_in.html')

    elif request.method == 'POST':
        is_auth = False

        db = get_db()

        # search provided user
        user = db.cursor().execute("SELECT user_id, password FROM user WHERE email_address=?",
            (
                request.form['email_address'],
            ))

        if user is not None:
            user_data = tuple(user.fetchone())

            db_user_id = user_data[0]
            db_hashed_pass = user_data[1]

            # password comparison
            if bcrypt.checkpw(request.form['password'].encode('utf-8'), db_hashed_pass):
                session['user_id'] = db_user_id
                session['email_address'] = request.form['email_address']
                is_auth = True

            else:
                return 'the password is wrong'

        else:
            return 'There is no user like that'
        db.close()
    if is_auth:
        # TODO: redirect mypage
        return redirect(url_for('show_my_page'))
    else:
        return 'Login failed'        


@app.route('/exam/answer_form', methods=['POST'])
def show_answer_form():
    print(sys._getframe().f_code.co_name)
    problems = []
    session['exam_id'] = request.form['exam_id']
    
    db = get_db()

    problems_object = db.cursor().execute('SELECT part_id, problem_id FROM problem WHERE exam_id=?', (session['exam_id'],))

    for problem in problems_object.fetchall():
        # [(part_id, problem_id), ...]
        problems.append(tuple(problem))

    db.close()
    return render_template('answer_form.html', problems=problems, exam_id=session['exam_id'])


@app.route('/insert_user_answer', methods=['POST'])
def insert_user_answer():

    answers = []
    for i in range(1, 201):
        answers.append(request.form[str(i)])

    try:
        db = get_db()
        cur = db.cursor()

        cur.execute('BEGIN;')
        cur.execute('INSERT INTO exam_date(exam_id, user_id, exam_date) VALUES (?, ?, ?);', 
            (
                session['user_id'],
                session['exam_id'],
                # exam_date
                datetime.now().strftime('%Y%m%d%H%M%S')
             ))

        exam_date_id = cur.lastrowid

        # insert user answer
        for idx, answer in enumerate(answers):
            cur.execute('INSERT INTO user_answer(exam_date_id, problem_id, user_answer) VALUES (?, ?, ?)', 
                (
                    exam_date_id,   # exam_date_id
                    idx + 1,     # problem_id
                    answer       # user_answer
                ))

        db.commit()
        #db.close()
        
        wrong_problem_ids = mark_user_answer(exam_date_id)
        
        total_ratio, part_ratios = caculate_answer_ratio(exam_date_id)

        insert_ratios(total_ratio, part_ratios, exam_date_id)

        db.close()
        return render_template('result.html', total_ratio=total_ratio, part_ratios=part_ratios, wrong_problem_ids=wrong_problem_ids)


    except sqlite3.Error as e:
        print(e)
        db.rollback()
        db.close()
        return


def insert_ratios(total_ratio, part_ratios, exam_date_id):

    db = get_db()

    db.cursor().execute('INSERT INTO total_answer_ratio(exam_date_id, total_ratio) VALUES (?, ?)', (exam_date_id, total_ratio))

    for part_id, part_ratio in part_ratios.items():
        db.cursor().execute('INSERT INTO part_answer_ratio(exam_date_id, part_id, part_ratio) VALUES (?, ?, ?)', (exam_date_id, part_id, part_ratio))

    db.commit()


def mark_user_answer(exam_date_id):

    wrong_problem_ids = []
    is_correct = ''
    sql = """
            SELECT ua.problem_id, ua.user_answer, p.correct_answer 
            FROM user_answer ua 
            INNER JOIN exam_date ed ON ua.exam_date_id = ed.exam_date_id 
            INNER JOIN problem p ON p.exam_id = ed.exam_id AND p.problem_id = ua.problem_id 
            WHERE ed.exam_date_id = ?
        """

    db = get_db()

    problem_answers = db.cursor().execute(sql, (exam_date_id,))

    for problem_answer in problem_answers:
        problem_id, user_answer, correct_answer = tuple(problem_answer)
        if user_answer == correct_answer:
            is_correct = 'T'
        else:
            is_correct = 'F'
            wrong_problem_ids.append(problem_id)

        db.cursor().execute('UPDATE user_answer SET is_correct = ? WHERE exam_date_id = ? AND problem_id = ?',
            (
                is_correct,
                exam_date_id,
                problem_id
            ))

    db.commit()

    return wrong_problem_ids


# return ratio (total, part) and insert into database
def caculate_answer_ratio(exam_date_id):
    print(sys._getframe().f_code.co_name)

    total_correct_count = 0  # cur.count by counting exam_date_id T
    part_correct_counts = {} # cur.count by counting part_id T
    part_problem_counts = {} # cur.count by counting same part_id
    total_ratio = 0          # total_correct_count / 200 * 100
    part_ratios = {}          # part_correct_counts / part_problem_counts * 100

    db = get_db()

    # select problem_id, part_id, use_answer, is_correct from ...

    correct_answer_objects = db.cursor().execute('SELECT problem_id FROM user_answer WHERE exam_date_id = ? AND is_correct = "T"', (exam_date_id,))
    total_correct_count = len(correct_answer_objects.fetchall())
    total_ratio = total_correct_count / 200 * 100

    sql = """
            SELECT ua.problem_id, p.part_id, ua.is_correct 
            FROM user_answer ua 
            INNER JOIN exam_date ed ON ua.exam_date_id = ed.exam_date_id 
            INNER JOIN problem p ON p.problem_id = ua.problem_id AND p.exam_id = ed.exam_id 
            WHERE ua.exam_date_id = ?
        """

    problems = db.cursor().execute(sql, (exam_date_id,))

    for problem in problems:
        problem_id, part_id, is_correct = tuple(problem)

        # couting problems by parts
        if part_id in part_problem_counts.keys():
            part_problem_counts[part_id] += 1
        else:
            part_problem_counts[part_id] = 1
        
        # counting corrects by parts
        if is_correct == 'T':
            if part_id in part_correct_counts.keys():
                part_correct_counts[part_id] += 1
            else:
                part_correct_counts[part_id] = 1

    # caculate ratio by parts
    part = 0
    for correct, count in zip(part_correct_counts.values(), part_problem_counts.values()):
        part += 1
        part_ratios[part] = round(correct / count * 100, 2)

    return total_ratio, part_ratios


@app.route('/logout')
def logout():
    session.pop('user_name', None)
    return redirect(url_for('login_form'))


@app.before_request
def csrf_protect():
    print(sys._getframe().f_code.co_name)
    if request.method == 'POST':
        token = session.pop('_csrf_token', None)

        if not token or token != request.form.get('_csrf_token'):
            abort(403)


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = str(os.urandom(24))

    return session['_csrf_token']


@app.route('/users/my_page')
def show_my_page():
    exams = get_exam_list()
    return render_template('my_page.html', exams=exams)


def get_exam_list():
    exams = []
    db = get_db()

    exams_object = db.cursor().execute('SELECT exam_id, exam_name FROM exam')
    
    for exam in exams_object.fetchall():
        # [(exam_id, exam_name), ...]
        exams.append(tuple(exam))

    db.close()

    return exams


if __name__ == '__main__':
    app.jinja_env.globals['csrf_token'] = generate_csrf_token
    app.run(debug=True)

