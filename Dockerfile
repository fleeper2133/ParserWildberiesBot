# Используем официальный образ Playwright с Python
FROM mcr.microsoft.com/playwright/python:v1.52.0

# Устанавливаем дополнительные зависимости
RUN apt-get update && \
    apt-get install -y \
    wget \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Настройка рабочей директории
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Команда запуска
CMD ["python", "telegram_bot.py"]