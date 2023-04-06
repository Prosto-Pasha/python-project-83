from psycopg2 import OperationalError
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def create_connection():
    """Возвращает подключение к базе PostgreSQL"""
    connection = None
    try:
        connection = psycopg2.connect(DATABASE_URL)
        connection.autocommit = True
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


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


def put_check(id, request_data):
    """
    Записывает результат проверки веб-сайта в таблицу url_checks
    :param id: int - id проверенного веб-сайта
    :param request_data: dict - результаты проверки веб-сайта
    :return:
    """
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
                VALUES (%s, %s, %s, %s, %s, %s);'''
            args = (
                id,
                request_data['status_code'],
                request_data['h1'],
                request_data['title'],
                request_data['description'],
                datetime.today()
            )
            curs.execute(query, args)
    except Exception as e:
        print('WARNING DATABASE: ', e)


def put_url(url):
    """
    Записывает новый url в таблицу urls
    и возвращает id записи
    :param url: имя веб-сайта
    :return: id новой записи
    """
    try:
        conn = create_connection()
        with conn.cursor() as curs:
            query = '''INSERT INTO urls (name, created_at)
                VALUES (%s, %s)
                RETURNING id'''
            args = (url, datetime.today())
            curs.execute(query, args)
            return curs.fetchone()[0]
    except Exception as e:
        print('WARNING DATABASE: ', e)
        return None


def get_url_id_from_db(url):
    """
    Возвращает id веб-сайта из таблицы urls
    найденный по имени url (если запись есть)
    :param url: str - имя веб-сайта
    :return: int - id веб-сайта или None
    """
    try:
        conn = create_connection()
        with conn.cursor() as curs:
            query = 'SELECT id FROM urls WHERE name=%s'
            args = (url,)
            curs.execute(query, args)
            return curs.fetchone()[0]
    except Exception as e:
        print('WARNING DATABASE: ', e)
        return None


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
