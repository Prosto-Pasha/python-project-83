import urllib.parse


def get_parsed_url(url):
    """
    Возвращает нормализованный адрес веб-сайта или пустую строку
    :param url: строка адрес веб-сайта
    :return: строка нормализованный адрес веб-сайта
    """
    parsed_url = urllib.parse.urlparse(url)
    url_scheme = parsed_url[0]
    url_netloc = parsed_url[1].lower().strip()
    conditions = (
        url_scheme not in ('http', 'https'),
        url_netloc == '',
        url_netloc.find(' ') > 0,
    )
    if any(conditions):
        return ''
    return f'{url_scheme}://{url_netloc}'
