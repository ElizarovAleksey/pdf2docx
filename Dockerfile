FROM python:3.10-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Создаём директорию приложения
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение
COPY . .

# Создаём папку для логов (если нет)
RUN mkdir -p logs

# Указываем порт
EXPOSE 8080

# Запуск приложения
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
