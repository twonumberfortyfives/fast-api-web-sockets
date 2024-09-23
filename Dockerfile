# Используйте официальный образ Python в качестве базового
FROM python:3.11-slim

# Установите рабочую директорию
WORKDIR /app

# Скопируйте зависимости
COPY requirements.txt .

# Установите зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Скопируйте весь проект в контейнер
COPY . .

# Укажите команду для запуска вашего FastAPI приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Откройте порт, на котором будет работать приложение
EXPOSE 8000
