from flask import Flask
from convert import convert_bp
import logging
from logging.handlers import RotatingFileHandler
import os

app = Flask(__name__)
app.register_blueprint(convert_bp)

if __name__ == '__main__':
    # Создание папки для логов, если не существует
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Настройка логгера
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=3)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    file_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Приложение запущено')

    # Запуск сервера
    app.run(host='0.0.0.0', port=8080)
