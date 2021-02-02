


from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g, make_response
# url_for - позволяет генерировать url-адрес по имени функции обработчика
import sqlite3
import os
from FDataBase import FDataBase
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from UserLogin import UserLogin
from flask_login import LoginManager, login_user, login_required


# конфигурация
DATABASE = '/tmp/flsite.db'
DEBUG = True
# SECRET_KEY = 'dsad23daefd23fsef45'

menu = [{'name': 'Installing', 'url': 'install-flask'},
        {'name': 'First app', 'url': 'first-app'},
        {'name': 'Contacts', 'url': 'contact'}]

app = Flask(__name__)
app.config['SECRET_KEY'] = '238a6152bb723cf0d24877ac57ab7d589a403e2b'
app.permanent_session_lifetime = datetime.timedelta(days=10)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))

login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    print('load_user')
    return UserLogin().fromDB(user_id, dbase)


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


dbase = None
@app.before_request
def before_request():
    """Устанавливаем соединение с БД перед выполнением запроса"""
    global dbase
    db = get_db()
    dbase = FDataBase(db)




@app.teardown_appcontext
def close_db(error):
    '''Закрываем соединение с БД, если оно было установлено'''
    if hasattr(g, 'link_db'):
        g.link_db.close()


# # Создадим представление
@app.route('/')
def index():
    return render_template('index.html', menu=dbase.get_menu(), posts=dbase.get_posts_anonce())


@app.route('/html_text')
def html_text():
    content = render_template('index.html', menu=menu, posts=[])
    res = make_response(content)
    res.headers['Content-Type'] = 'text/plain'
    res.headers['Server'] = 'flask_site_v.1'
    return res


@app.route('/img')
def img():
    img = None
    with app.open_resource( app.root_path + '/static/images/default.png', mode='rb') as f:
        img = f.read()

    if img is None:
        return "None image"
    res = make_response(img)
    res.headers['Content-Type'] = 'image/png'
    return res


@app.route('/error500')
def error500():
    res = make_response("<h1>Server error</h1>", 500)
    return res


data = [0]
@app.route('/session')
def session_data():
    session.permanent = False  # True сессии сохранятся даже если обновить/закрыть браузер
    if 'data' not in session:
        session['data'] = data  # обновление данных сессии
    else:
        session['data'][0] += 1  # запись данных в сессию
        session.modified = True
    return f"<h1>Session Page</h1><p>Quantity of views: {session['data']}"


@app.route("/add_post", methods=["POST", "GET"])
def add_post():
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
@login_required
def show_post(alias):
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

@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user = dbase.get_user_by_email(request.form['email'])
        if user and check_password_hash(user['psw'], request.form['psw']):
            userlogin = UserLogin().create(user)
            login_user(userlogin)
            return redirect(url_for('index'))

        flash("Wrong pair login/password", "error")

    return render_template('login.html', menu=dbase.get_menu(), title='Autorization')


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == 'POST':
        if len(request.form['name']) > 4 and len(request.form['email']) > 4 \
            and len(request.form['psw']) > 4 and request.form['psw'] == request.form['psw2']:
            hash = generate_password_hash(request.form['psw'])
            res = dbase.add_user(request.form['name'], request.form['email'], hash)
            if res:
                flash("Enter success", "success")
                return redirect(url_for('login'))
            else:
                flash("Add to Database error", "error")
        else:
            flash('Wrong field input', 'error')

    return render_template("register.html", menu=dbase.get_menu(), title="Регистрация")



@app.route('/logout')
def logout():
    res = make_response('<p>No autorization anymore!</p>')
    res.set_cookie('logged', '', 0)
    return res


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
@app.errorhandler(404)
def page_not_found(error):
    return render_template('page404.html', title="Page not found", menu=menu), 404


@app.route('/transfer')
def transfer():
    return redirect(url_for('index'), 301)




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
