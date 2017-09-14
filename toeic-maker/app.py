from flask import Flask, render_template, request
import sqlite3
import bcrypt

app = Flask(__name__)

DATABASE = '/tmp/toeic-maker.db'

# initialize database from schema.sql (sql_script)
@app.route('/create_db')
def init_db():
    conn = sqlite3.connect(DATABASE)
    # open db schema file
    with app.open_resource('schema.sql', 'r') as f:
        conn.cursor().executescript(f.read())
    conn.commit()
    conn.close()


@app.route('/user_add_form')
def user_add_form():
    return render_template('user_add.html')


@app.route('/user_create', methods=['POST'])
def user_create():

    if request.method == 'POST':
        conn = sqlite3.connect(DATABASE)

        # password hashing
        hashed_pass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        
        conn.cursor().execute("INSERT INTO user(user_name, password) VALUES (?, ?)", 
            (
                request.form['user_name'],
                hashed_pass
                ))
        conn.commit()
        conn.close()
        return 'User create successfully'

    return 'User create failed'


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        user_name = request.form['user_name']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        completion = False
        with conn:
            cur = conn.cursor()

            # search provided user
            rv = cur.execute("SELECT user_name, password FROM user WHERE user_name = ?;",
                (
                    user_name,
                ))

            # fetch target user's password (hashed)
            db_hashed_pass = rv.fetchone()[1]

            # compare provided password and hashed password in DB
            if bcrypt.checkpw(password.encode('utf-8'), db_hashed_pass):
                completion = True

    if completion:
        return 'Login successfully'
    else:
        return 'Login failed'


@app.route('/login_form')
def login_form():
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
