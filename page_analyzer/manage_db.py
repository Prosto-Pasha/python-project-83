from psycopg2 import OperationalError
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv
from page_analyzer.logger import get_logger


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


# Логирование
log = get_logger('manage_db')


def create_connection():
    """Возвращает подключение к базе PostgreSQL"""
    connection = None
    try:
        log.info('Connected to DB')
        connection = psycopg2.connect(DATABASE_URL)
        connection.autocommit = True
    except OperationalError as e:
        log.error(f'Error occurred while connecting to DB: {e}')
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
            log.info(f'Get check data for url with id={id} from DB')
    except Exception as e:
        log.error(f'Error occurred while getting check'
                  f' data for url with id={id} from DB: {e}')
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
            log.info('Get urls data from DB')
    except Exception as e:
        log.error(f'Error occurred while getting urls data from DB: {e}')
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
            log.info(f'Get data for url with id={id} from DB')
    except Exception as e:
        log.error(f'Error occurred while getting data'
                  f' for url with id={id} from DB: {e}')
    if url_data is None:
        log.error(f'Url with id={id} did not found in DB')
    else:
        result['id'] = url_data[0]
        result['name'] = url_data[1]
        result['created_at'] = url_data[2].strftime('%y-%m-%d')
    return result


def put_check(request_data):
    """
    Записывает результат проверки веб-сайта в таблицу url_checks
    :param request_data: tuple - результаты проверки веб-сайта
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
            args = (*request_data, datetime.today())
            curs.execute(query, args)
            log.info('Check data added in DB')
    except Exception as e:
        log.error(f'Error occurred while adding check data'
                  f' {request_data} in DB: {e}')


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
            log.info(f'Data for url {url} added in DB')
            return curs.fetchone()[0]
    except Exception as e:
        log.error(f'Error occurred while adding data'
                  f' for url {url} in DB: {e}')
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
            log.info(f'Get id for url {url} from DB')
            return curs.fetchone()[0]
    except Exception as e:
        log.error(f'Error occurred while getting id'
                  f' for url {url} from DB: {e}')
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
            log.info(f'Get url name for id={id} from DB')
    except Exception as e:
        log.error(f'Error occurred while getting url name'
                  f' for id={id} from DB: {e}')
    return result
