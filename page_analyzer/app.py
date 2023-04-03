from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    get_flashed_messages,
    make_response,
    # session,
)
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv
import urllib.parse

# Получаем переменные окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')

# Подключаемся к базе данных
conn = None
try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
except Exception as _ex:
    # TODO Добавить проверку на существование
    #  базы "database", и создание, если её нет
    print('[INFO] Error while connecting to database', _ex)


app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


@app.route('/')
def index():
    """
    Выводит начальную страницу
    :return: страница index.html
    """
    messages = get_flashed_messages()
    return render_template('index.html', messages=messages)


@app.route('/urls', methods=['POST'])
def urls_post():
    """
    Обрабатывает добавление нового адреса веб-сайта
    Вызывыет процедуру url_get или сообщение об ошибке
    :return: переадресация на страницу index.html или checks.html
    """
    new_url = request.form['url']
    parsed_url = get_parsed_url(new_url)
    if parsed_url == '':
        flash('Некорректный URL', 'error')
        response = make_response(redirect(url_for('index'), code=302))
        return response
    url_id = get_url_id(parsed_url)
    response = make_response(redirect(url_for(
        'url_get',
        id=url_id
    ), code=302))
    return response


@app.route('/urls/<id>')
def url_get(id):
    """
    Открывает страницу checks.html для веб-сайта
    с id в таблице urls
    :return: переадресация на страницу checks.html
    """
    url_data = get_url_data(id)
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'checks.html',
        url=url_data,
        id=id,
        messages=messages,
        # url_checks=url_checks, # проверки
    )


@app.route('/urls')
def urls_get():
    urls_data = get_urls_data()
    return render_template('urls.html', urls=urls_data,)


def get_urls_data():
    """
    Возвращает все данные из таблицы urls
    :return: dict - словарь с данными таблицы urls
    """
    urls_data = None
    try:
        with conn.cursor() as curs:
            # TODO Добавить объединение с таблицей проверок
            #  и заполнение кода возврата
            query = "SELECT id," \
                    " name," \
                    " to_char(created_at, 'YYYY-MM-DD') AS date_add," \
                    " 'Код возврата' AS Code" \
                    " FROM urls" \
                    " ORDER BY created_at DESC"
            curs.execute(query)
            urls_data = curs.fetchall()
    except Exception as e:
        print('WARNING DATABASE: ', e)
    return urls_data


def get_url_data(id):
    """
    Возвращает данные веб-сайта из таблицы urls
    по переданному id
    :param id: int - id веб-сайта в таблице urls
    :return: dict - словарь с данными веб-сайта
    """
    url_data = None
    result = {}
    try:
        with conn.cursor() as curs:
            query = 'SELECT * FROM urls WHERE id=%s'
            args = (id,)
            curs.execute(query, args)
            url_data = curs.fetchone()
    except Exception as e:
        print('WARNING DATABASE: ', e)
    if url_data is None:
        print(f'Не найден url с id={id}!')
    else:
        result['id'] = url_data[0]
        result['name'] = url_data[1]
        result['created_at'] = url_data[2].strftime('%y-%m-%d')
    return result


def get_parsed_url(url):
    """
    Возвращает нормализованный адрес веб-сайта
    Если есть ошибки, то возвращает пустую строку
    :param url: строка адрес веб-сайта
    :return: строка нормализованный адрес веб-сайта
    """
    parsed_url = urllib.parse.urlparse(url)
    url_scheme = parsed_url[0]
    url_netloc = parsed_url[1].lower().strip()
    if url_scheme == ''\
            or url_netloc == ''\
            or url_netloc.find(' ') > 0:
        return ''
    return f'{url_scheme}://{url_netloc}'


def get_url_id(url):
    """
    Проверяет наличие адреса url в таблице urls
    При необходимости делает новую запись
    :param url: строка нормализованный адрес веб-сайта
    :return: url_id: int - id для url в таблице urls
    """
    url_id = None
    try:
        with conn.cursor() as curs:
            query = 'SELECT id FROM urls WHERE name=%s'
            args = (url,)
            curs.execute(query, args)
            url_id = curs.fetchone()[0]
    except Exception as e:
        print('WARNING DATABASE: ', e)
    if url_id is None:
        with conn.cursor() as curs:
            query = '''INSERT INTO urls (name, created_at)
                VALUES (%s, %s)
                RETURNING id'''
            args = (url, datetime.today())
            curs.execute(query, args)
            url_id = curs.fetchone()[0]
            flash('Страница успешно добавлена', 'alert alert-success')
    else:
        flash('Страница уже существует', 'alert alert-info')
    return url_id


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
