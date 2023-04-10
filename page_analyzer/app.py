from flask import (Flask, render_template, request, redirect, url_for,
                   flash, get_flashed_messages, make_response,)
import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from page_analyzer.parse_url import get_parsed_url
from page_analyzer.manage_db import (
    get_url_data, get_url_checks, get_urls_data, put_check,
    put_url, get_url_id_from_db, get_url_name
)
from page_analyzer.logger import get_logger


# Получаем переменные окружения
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


# Логирование
log = get_logger('app')


@app.route('/')
def index():
    """
    Выводит начальную страницу
    :return: страница index.html
    """
    log.info('Open index.html')
    return render_template('index.html', messages=get_flashed_messages())


@app.route('/urls', methods=['POST'])
def urls_post():
    """
    Обрабатывает добавление нового адреса веб-сайта
    Вызывыет процедуру url_get или сообщение об ошибке
    :return: переадресация на страницу index.html или checks.html
    """
    new_url = request.form['url']
    log.info(f'Input url {new_url}')
    parsed_url = get_parsed_url(new_url)
    log.info(f'Parsed url "{parsed_url}"')
    if parsed_url == '':
        flash('Некорректный URL', 'error')
        messages = get_flashed_messages()
        return render_template('index.html', messages=messages), 422
    url_id, new_url = get_url_id(parsed_url)
    if new_url:
        flash('Страница успешно добавлена', 'alert alert-success')
        log.info(f'Parsed url {parsed_url} added')
    else:
        flash('Страница уже существует', 'alert alert-info')
        log.info(f'Parsed url {parsed_url} already exist')
    response = make_response(redirect(url_for('url_get', id=url_id)))
    return response


@app.route('/urls/<id>')
def url_get(id):
    """
    Открывает страницу checks.html для веб-сайта с id в таблице urls
    :return: страница checks.html
    """
    log.info('Open checks.html')
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
    log.info('Open urls.html')
    return render_template('urls.html', urls=get_urls_data(),)


@app.route('/urls/<id>/checks', methods=['POST'])
def check_url(id):
    """
    Выполняет проверку для веб-сайта из таблицы urls с id
    При удачной проверке, записывает результат в таблицу url_checks
    :param id: int - id веб-сайта в таблице urls
    :return: страница checks.html для веб-сайта id
    """
    request_data = get_url_request(get_url_name(id))
    if request_data is None:
        log.error(f'Error occurred while checking url {get_url_name(id)}')
        flash('Произошла ошибка при проверке', 'alert alert-danger')
    else:
        log.info(f'Url {get_url_name(id)} successfully checked')
        flash('Страница успешно проверена', 'alert alert-success')
    put_check(id, request_data)
    return redirect(url_for('url_get', id=id))


def get_url_request(url):
    """
    Возвращает нужные данные ответа веб-сайта в виде словаря
    :param url: str - имя веб-сайта
    :return: dict или None, если произошла ошибка
    """
    try:
        log.info(f'Requesting {url} data')
        answer = requests.get(url)
        answer.raise_for_status()
        bs_r = get_site_data(answer)
        result = {
            'status_code': answer.status_code,
            'h1': bs_r['h1'],
            'title': bs_r['title'],
            'description': bs_r['description']
        }
        return result
    except requests.exceptions.RequestException:
        log.error(f'Error occurred while getting {url} request')
        return None


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
    log.info('Getting url data')
    return result


def get_url_id(url):
    """
    Проверяет наличие адреса url в таблице urls. Если её нет, добавляет запись
    :param url: строка нормализованный адрес веб-сайта
    :return: (url_id, new_url): tuple
        - url_id - int - id для url в таблице urls,
        - new_url - bool - признак записи нового url
    """
    log.info(f'Getting {url} id')
    url_id = get_url_id_from_db(url)
    if url_id is None:
        return put_url(url), True
    return url_id, False


if __name__ == '__main__':
    log.info('Starting app...')
    app.run(host='0.0.0.0', port=5000, debug=True)
