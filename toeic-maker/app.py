from flask import Flask,  g
import sqlite3

app = Flask(__name__)

DATABASE = '/tmp/toeic-maker.db'

@app.route('/get_db')
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()



# this is just command of the database initialization
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        


@app.route('/login')
def login():
    pass 




# storing user answer into db
def submit_answer():
    pass


if __name__ == '__main__':
    app.run(debug=True)
