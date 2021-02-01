


from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g
# url_for - позволяет генерировать url-адрес по имени функции обработчика
import sqlite3
import os
from FDataBase import FDataBase


# конфигурация
DATABASE = '/tmp/flsite.db'
DEBUG = True
SECRET_KEY = 'dsad23daefd23fsef45'


app = Flask(__name__)
# app.config['SECRET_KEY'] = 'hdsfksjhfjdshfjsdhflsdhf3jfi'
#
# menu = [{'name': 'Installing', 'url': 'install-flask'},
#         {'name': 'First app', 'url': 'first-app'},
#         {'name': 'Contacts', 'url': 'contact'}]
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    """Вспомогательная функция для создания таблиц БД"""
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


def get_db():
    '''Соединение с БД, если оно еще не установлено'''
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


@app.teardown_appcontext
def close_db(error):
    '''Закрываем соединение с БД, если оно было установлено'''
    if hasattr(g, 'link_db'):
        g.link_db.close()


# # Создадим представление
@app.route('/')
def index():
    db = get_db()
    dbase = FDataBase(db)
    # print(url_for('index'))
    return render_template('index.html', menu=dbase.get_menu(), posts=dbase.get_posts_anonce())


@app.route("/add_post", methods=["POST", "GET"])
def add_post():
    db = get_db()
    dbase = FDataBase(db)

    if request.method == "POST":
        if len(request.form['name']) > 4 and len(request.form['post']) > 10:
            res = dbase.add_post(request.form['name'], request.form['post'], request.form['url'])
            if not res:
                flash('Add post error', category = 'error')
            else:
                flash('Add post success', category='success')
        else:
            flash('Add post error', category='error')

    return render_template('add_post.html', menu = dbase.get_menu(), title="Add post")


@app.route("/post/<alias>")
# @login_required
def show_post(alias):
    db = get_db()
    dbase = FDataBase(db)
    title, post = dbase.get_post(alias)
    if not title:
        abort(404)

    return render_template('post.html', menu=dbase.get_menu(), title=title, post=post)





# @app.route('/about')
# def about():
#     print(url_for('about'))
#     return render_template('about.html', title="О сайте", menu=menu)
#
#
# @app.route('/contact', methods=['POST', 'GET'])
# def contact():
#     if request.method == 'POST':
#         if len(request.form['username']) > 2:
#             flash('Message send', category='success')
#         else:
#             flash("Send Error", category='error')
#
#         print(request.form)
#
#     return render_template('contact.html', title="Contacts", menu=menu)
#
#
# @app.route('/profile/<username>')  # Все что написано после конвеpтера path поместить в переменную username
# # Еще конвертеры:
# # int - только числа
# # float - можно записывать число с плавающей точнок
# def profile(username):
#     if 'userLogged' not in session or session['userLogged'] != username:
#         abort(401)
#
#     return f'User: {username}'
#
#
# @app.route('/login', methods=['POST', 'GET'])
# def login():
#     if 'userLogged' in session:
#         return redirect(url_for('profile', username=session['userLogged']))
#     elif request.method == 'POST' and request.form['username'] == 'roman' and request.form['psw'] == '123':
#         session['userLogged'] = request.form['username']
#         return redirect(url_for('profile', username=session['userLogged']))
#
#     return render_template('login.html', title='Autorization', menu=menu)
#
#
# @app.errorhandler(404)
# def page_not_found(error):
#     return render_template('page404.html', title="Page not found", menu=menu), 404
#
#
#
# # with app.test_request_context():
# #     print(url_for('index'))
# #     print(url_for('about'))
# #     print(url_for('profile', username='roman'))
#
if __name__ == '__main__':
    app.run(debug=True)
    # чтобы ошибки выводились в консоль, но на продакшене нужно указать False чтобы ошибки не были
    # видны пользователю.
#
#
