"""Скрипт для заполнения базы тестовыми данными"""
import sys
import requests
import random

sys.path.append('.')

API_URL = "http://localhost:8000/api"


def create_vacancies():
    vacancies = [
        {
            "title": "Python Developer",
            "description": "Мы ищем опытного Python разработчика для работы над высоконагруженным проектом. Стек: FastAPI, PostgreSQL, Docker.",
            "requirements": "Python 3.10+, SQL, Docker, Git",
            "salary_min": 150000,
            "salary_max": 250000,
            "location": "Москва",
            "employer_id": 1
        },
        {
            "title": "Data Scientist",
            "description": "Разработка ML моделей для рекомендательной системы. NLP, PyTorch, Scikit-learn.",
            "requirements": "Python, ML, DL, SQL, Pandas",
            "salary_min": 200000,
            "salary_max": 350000,
            "location": "Удаленно",
            "employer_id": 1
        },
        {
            "title": "Frontend Developer (React)",
            "description": "Разработка интерфейсов на React.js. Работа в команде с дизайнерами и бекендерами.",
            "requirements": "JS, React, HTML5, CSS3, Webpack",
            "salary_min": 120000,
            "salary_max": 180000,
            "location": "Санкт-Петербург",
            "employer_id": 1
        },
        {
            "title": "DevOps Engineer",
            "description": "Настройка CI/CD пайплайнов, поддержка инфраструктуры в облаке.",
            "requirements": "Linux, Docker, Kubernetes, Jenkins, AWS",
            "salary_min": 180000,
            "salary_max": 300000,
            "location": "Москва",
            "employer_id": 1
        },
        {
            "title": "QA Engineer (Manual)",
            "description": "Ручное тестирование веб-приложений. Написание тест-кейсов, работа в Jira.",
            "requirements": "Понимание процессов QA, SQL, API testing",
            "salary_min": 80000,
            "salary_max": 120000,
            "location": "Екатеринбург",
            "employer_id": 1
        }
    ]

    print("🚀 Создаем вакансии...")

    for v in vacancies:
        try:
            # Сначала нужно создать пользователя (работодателя) если нет
            # Но для упрощения просто пробуем создать вакансию
            # Если employer_id=1 нет, нужно сначала создать юзера

            # Пробуем создать вакансию
            response = requests.post(f"{API_URL}/vacancies/", json=v)

            if response.status_code == 200:
                print(f"✅ Создана: {v['title']}")
            else:
                print(f"❌ Ошибка {response.status_code}: {response.text}")

        except Exception as e:
            print(f"❌ Ошибка соединения: {e}")


if __name__ == "__main__":
    create_vacancies()
