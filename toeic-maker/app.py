from flask import Flask, render_template, request
import sqlite3

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
        conn.cursor().execute("INSERT INTO user(first_name, last_name, password) VALUES (?, ?, ?)", 
            (
                request.form['first_name'],
                request.form['last_name'],
                request.form['password']
                ))
        conn.commit()
        conn.close()
        return 'User create successfully'

    return 'User create failed'




if __name__ == '__main__':
    app.run(debug=True)
