from flask import Flask, render_template, request, g, session
import os
import sqlite3
import bcrypt
from datetime import datetime

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


@app.route('/user_add_form')
def user_add_form():
    return render_template('user_add.html')


@app.route('/user_create', methods=['POST'])
def user_create():

    if request.method == 'POST':
        db = get_db()
        # conn = sqlite3.connect(DATABASE)

        # password hashing
        hashed_pass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        
        db.cursor().execute("INSERT INTO user(user_name, password) VALUES (?, ?)", 
            (
                request.form['user_name'],
                hashed_pass
                ))
        db.commit()
        db.close()
        return 'User create successfully'

    return 'User create failed'


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        session['user_name'] = request.form['user_name']
        password = request.form['password']

        db = get_db()

        completion = False

        # search provided user
        rv = db.cursor().execute("SELECT password, user_id FROM user WHERE user_name = ?;",
            (
                session['user_name'],
            ))

        for r in rv:
            # fetch target user's password (hashed)
            db_hashed_pass = r[0]
            session['user_id'] = r[1]

        # compare provided password and hashed password in DB
        if bcrypt.checkpw(password.encode('utf-8'), db_hashed_pass):
            completion = True
        print(session['user_id'])

    if completion:
        return 'Login successfully'
    else:
        return 'Login failed'


@app.route('/login_form')
def login_form():
    return render_template('login.html')


@app.route('/')
def index():
    return render_template('index.html')


# render answer form
@app.route('/answer_form/<int:exam_id>')
def answer_form(exam_id):
    db = get_db()

    session['exam_id'] = exam_id

    problems = []
    # part1 to 7
    for i in range(1, 8):
        rv = db.cursor().execute('SELECT part_id, problem_id FROM problem WHERE exam_id=? AND part_id=?;',
            (
                exam_id,
                i
            ))

        for r in rv:
            # (part_id, problem_id)
            tmp = (r[0], r[1])
            # [(part_id, problem_id), ...]
            problems.append(tmp)

    db.close()

    return render_template('answer_form.html', problems=problems, exam_id=exam_id)


@app.route('/save_user_answer', methods=['POST'])
def save_user_answer():
    
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

        lastrowid = cur.lastrowid

        # iterate 1 to 200 for problem counts
        for i in range(1,201):
            cur.execute('INSERT INTO user_answer(exam_date_id, problem_id, user_answer) VALUES (?, ?, ?)', 
                (
                    lastrowid,            # exam_date_id
                    i,                    # problem_id
                    request.form[str(i)]  # user_answer
                ))

        db.commit()
        db.close()

    except sqlite3.Error as e:
        print(e) # エラー
        db.rollback()
        db.close()



if __name__ == '__main__':
    app.run(debug=True)
