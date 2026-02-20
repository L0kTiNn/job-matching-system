"""Подключение к PostgreSQL и работа с векторами"""

import psycopg2
from psycopg2.extras import execute_values
import numpy as np
from typing import List, Tuple, Dict, Optional


class DatabaseManager:
    """Класс для работы с PostgreSQL и pgvector"""

    def __init__(self, host="localhost", port=5432, database="job_matching_system",
                 user="postgres", password="diploma2025"):
        """Инициализация подключения к БД"""
        self.connection_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
        self.conn = None
        self.cursor = None

    def connect(self):
        """Подключение к базе данных"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.cursor = self.conn.cursor()
            print(" Подключение к БД успешно")
        except Exception as e:
            print(f" Ошибка подключения к БД: {e}")
            raise

    def close(self):
        """Закрытие подключения"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Подключение к БД закрыто")

    def save_resume_embedding(self, resume_id: int, embedding: np.ndarray):
        """
        Сохранение эмбеддинга резюме в БД

        Args:
            resume_id: ID резюме
            embedding: векторное представление (768 размерность)
        """
        embedding_list = embedding.tolist()

        query = """
        UPDATE resumes 
        SET embedding = %s::vector 
        WHERE id = %s
        """

        self.cursor.execute(query, (embedding_list, resume_id))
        self.conn.commit()

    def save_vacancy_embedding(self, vacancy_id: int, embedding: np.ndarray):
        """
        Сохранение эмбеддинга вакансии в БД

        Args:
            vacancy_id: ID вакансии
            embedding: векторное представление
        """
        embedding_list = embedding.tolist()

        query = """
        UPDATE vacancies 
        SET embedding = %s::vector 
        WHERE id = %s
        """

        self.cursor.execute(query, (embedding_list, vacancy_id))
        self.conn.commit()

    def get_all_resumes(self) -> List[Dict]:
        """Получить все резюме из БД"""
        query = """
        SELECT id, user_id, title, summary, skills, experience, education,
               desired_position, desired_salary, location
        FROM resumes
        WHERE is_active = true
        """

        self.cursor.execute(query)
        columns = [desc[0] for desc in self.cursor.description]

        results = []
        for row in self.cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results

    def get_all_vacancies(self) -> List[Dict]:
        """Получить все вакансии из БД"""
        query = """
        SELECT id, employer_id, title, description, requirements,
               salary_min, salary_max, location
        FROM vacancies
        WHERE is_active = true
        """

        self.cursor.execute(query)
        columns = [desc[0] for desc in self.cursor.description]

        results = []
        for row in self.cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results

    def find_similar_vacancies(self, resume_id: int, limit: int = 10) -> List[Tuple[int, str, float]]:
        """
        Поиск похожих вакансий для резюме по векторному сходству

        Args:
            resume_id: ID резюме
            limit: количество результатов

        Returns:
            Список кортежей (vacancy_id, title, description, salary_min, salary_max, location, similarity)
        """
        query = """
        SELECT 
            v.id,
            v.title,
            v.description,
            v.salary_min,
            v.salary_max,
            v.location,
            1 - (v.embedding <=> r.embedding) as similarity
        FROM vacancies v
        CROSS JOIN resumes r
        WHERE r.id = %s 
          AND v.is_active = true
          AND v.embedding IS NOT NULL
          AND r.embedding IS NOT NULL
        ORDER BY v.embedding <=> r.embedding
        LIMIT %s
        """

        self.cursor.execute(query, (resume_id, limit))
        return self.cursor.fetchall()

    def find_similar_resumes(self, vacancy_id: int, limit: int = 10) -> List[Tuple]:
        """
        Поиск похожих резюме для вакансии через cosine similarity

        Args:
            vacancy_id: ID вакансии
            limit: количество результатов

        Returns:
            Список кортежей: (id, title, skills, experience, education,
                             desired_position, desired_salary, location, similarity)
        """
        query = """
        SELECT 
            r.id,
            r.title,
            r.skills,
            r.experience,
            r.education,
            r.desired_position,
            r.desired_salary,
            r.location,
            1 - (r.embedding <=> v.embedding) as similarity
        FROM resumes r
        CROSS JOIN vacancies v
        WHERE v.id = %s 
          AND r.is_active = true
          AND r.embedding IS NOT NULL
          AND v.embedding IS NOT NULL
        ORDER BY r.embedding <=> v.embedding
        LIMIT %s
        """

        self.cursor.execute(query, (vacancy_id, limit))
        return self.cursor.fetchall()


# Тест подключения
if __name__ == "__main__":
    db = DatabaseManager()

    try:
        db.connect()

        # Получить резюме
        resumes = db.get_all_resumes()
        print(f"\n📄 Найдено резюме: {len(resumes)}")
        for resume in resumes:
            print(f"  - {resume['title']} (ID: {resume['id']})")

        # Получить вакансии
        vacancies = db.get_all_vacancies()
        print(f"\n Найдено вакансий: {len(vacancies)}")
        for vacancy in vacancies:
            print(f"  - {vacancy['title']} (ID: {vacancy['id']})")

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        db.close()
