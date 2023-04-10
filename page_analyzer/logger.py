import logging
import os
from logging.handlers import RotatingFileHandler


LOG_FOLDER = 'log'
LOGGING_LEVEL = logging.ERROR  # logging.INFO


def create_log_folder(folder=LOG_FOLDER):
    """
    Создаёт (при необходимости) каталог LOG_FOLDER
    :param folder:
    :return:
    """
    if not os.path.exists(folder):
        os.mkdir(folder)


def get_logger(name='log'):
    """
    Создаёт лог-файл с именем name в папке LOG_FOLDER
    Возвращает логгер с именем name
    :param name: str - имя логгера и файла
    :return: logger
    """
    create_log_folder()
    file_path = os.sep.join([LOG_FOLDER, f'{name}.log'])
    log = logging.getLogger(name)
    log.setLevel(LOGGING_LEVEL)
    handler = RotatingFileHandler(
        file_path,
        mode='a',
        maxBytes=5000,
        backupCount=2,
        encoding='utf-8'
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    log.addHandler(handler)
    return log
