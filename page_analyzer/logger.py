import logging
import os
from logging.handlers import RotatingFileHandler


LOG_FOLDER = 'log'
LOGGING_LEVEL = logging.INFO
# Debug (10), Info (20), Warning (30), Error (40), Critical (50)


def create_log_folder(folder=LOG_FOLDER):
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
    handler = logging.handlers.RotatingFileHandler(
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
