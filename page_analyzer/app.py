from flask import (Flask, render_template, request, redirect, url_for,
                   flash, get_flashed_messages, make_response,)
from psycopg2 import OperationalError
import psycopg2
import os
import requests
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Получаем переменные окружения
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')

# Подключаемся к базе данных
# conn = psycopg2.connect(DATABASE_URL)
# conn.autocommit = True

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


def create_connection():
    """Возвращает подключение к базе SQL"""
    connection = None
    try:
        connection = psycopg2.connect(DATABASE_URL)
        connection.autocommit = True
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


@app.route('/')
def index():
    """
    Выводит начальную страницу
    :return: страница index.html
    """
    return render_template('index.html', messages=get_flashed_messages())


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
        response = make_response(render_template(
            'index.html',
            messages=get_flashed_messages())
        )
        return response
    url_id = get_url_id(parsed_url)
    response = make_response(redirect(url_for(
        'url_get',
        id=url_id
    )))
    return response


@app.route('/urls/<id>')
def url_get(id):
    """
    Открывает страницу checks.html для веб-сайта с id в таблице urls
    :return: переадресация на страницу checks.html
    """
    return render_template(
        'checks.html',
        url=get_url_data(id),
        messages=get_flashed_messages(with_categories=True),
        checks=get_url_checks(id),
    )


@app.route('/urls')
def urls_get():
    """
    Открывает страницу urls.html со списком сайтов
    :return: страница urls.html
    """
    return render_template('urls.html', urls=get_urls_data(),)


@app.route('/urls/<id>/checks', methods=['POST'])
def check_url(id):
    """
    Запускает проверку веб-сайта из таблицы urls с id. Результат проверки
    записывается в url_checks. После этого страница checks.html обновляется
    :param id: int - id веб-сайта в таблице urls
    :return: страница checks.html для веб-сайта id
    """
    make_check(id)
    return redirect(url_for('url_get', id=id))


def get_url_checks(id):
    """
    Возвращает все данные из таблицы url_checks для веб-сайта с id
    :param id: int - id веб-сайта в таблице urls
    :return: - данные таблицы urls
    """
    checks_data = None
    try:
        conn = create_connection()
        with conn.cursor() as curs:
            query = '''SELECT id,
                        status_code,
                        h1,
                        title,
                        description,
                        to_char(created_at, 'YYYY-MM-DD') AS date_add
                    FROM url_checks
                    WHERE url_id=%s
                    ORDER BY created_at DESC;'''
            curs.execute(query, (id, ))
            checks_data = curs.fetchall()
    except Exception as e:
        print('WARNING DATABASE: ', e)
    return checks_data


def make_check(id):
    """
    Выполняет проверку для веб-сайта из таблицы urls с id
    При удачной проверке, записывает результат в таблицу url_checks
    :param id: int - id веб-сайта в таблице urls
    """
    request_data = get_url_request(get_url_name(id))
    check_data = None
    try:
        conn = create_connection()
        with conn.cursor() as curs:
            query = '''INSERT INTO url_checks (
                    url_id,
                    status_code,
                    h1,
                    title,
                    description,
                    created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;'''
            args = (
                id,
                request_data['status_code'],
                request_data['h1'],
                request_data['title'],
                request_data['description'],
                datetime.today()
            )
            curs.execute(query, args)
            check_data = curs.fetchone()[0]
    except Exception as e:
        print('WARNING DATABASE: ', e)
    return check_data is not None


def get_url_request(url):
    """
    Возвращает нужные данные ответа веб-сайта в виде словаря
    :param url: str - имя веб-сайта
    :return: dict или None, если произошла ошибка
    """
    err_class = 'alert alert-danger'
    try:
        answer = requests.get(url)
    except requests.exceptions.Timeout:
        flash('Произошла ошибка при проверке', err_class)  # (Timeout)
        return None
    except requests.exceptions.TooManyRedirects:
        flash('Произошла ошибка при проверке', err_class)  # (2 many redirects)
        return None
    except requests.exceptions.RequestException:  # as e
        flash('Произошла ошибка при проверке', err_class)  # {e}
        return None
    flash('Страница успешно проверена', 'alert alert-success')
    bs_r = get_site_data(answer)
    result = {
        'status_code': answer.status_code,
        'h1': bs_r['h1'],
        'title': bs_r['title'],
        'description': bs_r['description']
    }
    return result


def get_site_data(answer):
    """
    С библиотекой bs4 получаем дополнительную информацию из ответа веб-сайта
    :param answer: ответ веб-сайта (библиотека requests)
    :return: dict словарь с нужными данными из ответа
    """
    soup = BeautifulSoup(answer.text, "html.parser")
    result = {'h1': '', 'title': '', 'description': ''}
    if soup.h1 is not None:
        result['h1'] = soup.h1.text
    if soup.title is not None:
        result['title'] = soup.title.string
    description = soup.find("meta", {"name": "description"})
    if description is not None:
        result['description'] = description['content']
    return result


def get_urls_data():
    """
    Возвращает все данные из таблицы urls
    :return: ? - данные таблицы urls
    """
    urls_data = None
    try:
        conn = create_connection()
        with conn.cursor() as curs:
            query = '''
SELECT urls.id         AS id,
    urls.NAME          AS NAME,
    checks.check_date  AS check_date,
    checks.status_code AS status_code
FROM urls
    LEFT OUTER JOIN (SELECT url_checks.status_code        AS status_code,
            url_checks2.url_id                            AS url_id,
            To_char(url_checks2.created_at, 'YYYY-MM-DD') AS check_date
        FROM url_checks
            JOIN (SELECT url_checks.url_id AS url_id,
                Max(url_checks.created_at) AS created_at
            FROM url_checks
                GROUP BY url_checks.url_id) AS url_checks2
                ON url_checks.url_id = url_checks2.url_id
                AND url_checks.created_at = url_checks2.created_at) AS checks
    ON urls.id = checks.url_id
ORDER BY urls.created_at DESC;'''
            curs.execute(query)
            urls_data = curs.fetchall()
    except Exception as e:
        print('WARNING DATABASE: ', e)
    return urls_data


def get_url_data(id):
    """
    Возвращает данные веб-сайта из таблицы urls по переданному id
    :param id: int - id веб-сайта в таблице urls
    :return: dict - словарь с данными веб-сайта
    """
    url_data = None
    result = {}
    try:
        conn = create_connection()
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
    Возвращает нормализованный адрес веб-сайта или пустую строку
    :param url: строка адрес веб-сайта
    :return: строка нормализованный адрес веб-сайта
    """
    parsed_url = urllib.parse.urlparse(url)
    url_scheme = parsed_url[0]
    url_netloc = parsed_url[1].lower().strip()
    if url_scheme == '' or url_netloc == '' or url_netloc.find(' ') > 0:
        return ''
    return f'{url_scheme}://{url_netloc}'


def get_url_name(id):
    """
    Возвращает имя веб-сайта по его id из таблицы urls
    :param id: int - id веб-сайта в таблице urls
    :return: str - name имя веб-сайта в таблице urls
    """
    result = None
    try:
        conn = create_connection()
        with conn.cursor() as curs:
            query = 'SELECT name FROM urls WHERE id=%s'
            args = (id,)
            curs.execute(query, args)
            result = curs.fetchone()[0]
    except Exception as e:
        print('WARNING DATABASE: ', e)
    return result


def get_url_id(url):
    """
    Проверяет наличие адреса url в таблице urls. Если её нет, добавляет запись
    :param url: строка нормализованный адрес веб-сайта
    :return: url_id: int - id для url в таблице urls
    """
    url_id = None
    try:
        conn = create_connection()
        with conn.cursor() as curs:
            query = 'SELECT id FROM urls WHERE name=%s'
            args = (url,)
            curs.execute(query, args)
            url_id = curs.fetchone()[0]
    except Exception as e:
        print('WARNING DATABASE: ', e)
    if url_id is None:
        conn = create_connection()
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
