"""
Скрипт для генерации УМНЫХ эмбеддингов для всех резюме и вакансий
ВЕРСИЯ 2.0: multilingual модель (768 измерений) + сравнение навыков!
"""

import sys
sys.path.append('.')

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import psycopg2
import numpy as np

# ============= КОНФИГУРАЦИЯ =============

DB_CONFIG = {
    "host": "localhost",
    "database": "job_matching_system",
    "user": "postgres",
    "password": "diploma2025"
}

# Multilingual модель с 768 измерениями
MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'

# ============= ИНИЦИАЛИЗАЦИЯ =============

print("=" * 60)
print(" ПРОКАЧАННАЯ ГЕНЕРАЦИЯ ЭМБЕДДИНГОВ V2.0")
print("=" * 60)
print(f"\n Загрузка модели: {MODEL_NAME}...")

model = SentenceTransformer(MODEL_NAME)
print(" Модель загружена!\n")

# ============= ФУНКЦИИ =============

def get_db_connection():
    """Подключение к БД"""
    return psycopg2.connect(**DB_CONFIG)

def normalize_skill(skill: str) -> str:
    """Нормализация навыка"""
    return skill.lower().strip()

def generate_skill_embeddings():
    """Генерация эмбеддингов для КАЖДОГО уникального навыка"""

    conn = get_db_connection()
    cur = conn.cursor()

    print("=" * 60)
    print("ЭТАП 1: ГЕНЕРАЦИЯ ЭМБЕДДИНГОВ НАВЫКОВ")
    print("=" * 60)

    # Собираем ВСЕ уникальные навыки
    all_skills = set()

    # Из резюме
    cur.execute("SELECT skills FROM resumes WHERE skills IS NOT NULL")
    for (skills_str,) in cur.fetchall():
        if skills_str:
            skills = [normalize_skill(s.strip()) for s in skills_str.split(',') if s.strip()]
            all_skills.update(skills)

    # Из вакансий
    cur.execute("SELECT requirements FROM vacancies WHERE requirements IS NOT NULL")
    for (req_str,) in cur.fetchall():
        if req_str:
            skills = [normalize_skill(s.strip()) for s in req_str.split(',') if s.strip()]
            all_skills.update(skills)

    print(f"\n Найдено уникальных навыков: {len(all_skills)}\n")

    # Создаём таблицу если нет
    cur.execute("""
        CREATE TABLE IF NOT EXISTS skill_embeddings (
            id SERIAL PRIMARY KEY,
            skill_text VARCHAR(255) NOT NULL UNIQUE,
            embedding VECTOR(768) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Создаём индексы
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_skill_embeddings_text 
        ON skill_embeddings(skill_text)
    """)

    conn.commit()

    # Генерируем эмбеддинги
    processed = 0
    for skill in sorted(all_skills):
        try:
            embedding = model.encode(skill)
            embedding_list = embedding.tolist()

            cur.execute("""
                INSERT INTO skill_embeddings (skill_text, embedding)
                VALUES (%s, %s)
                ON CONFLICT (skill_text) DO NOTHING
            """, (skill, embedding_list))

            processed += 1

            if processed % 10 == 0:
                print(f" Обработано: {processed}/{len(all_skills)}")

        except Exception as e:
            print(f" Ошибка для навыка '{skill}': {e}")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n Эмбеддинги сгенерированы для {len(all_skills)} навыков!\n")

def generate_resume_embeddings():
    """Генерация эмбеддингов для резюме"""

    conn = get_db_connection()
    cur = conn.cursor()

    print("=" * 60)
    print("ЭТАП 2: ГЕНЕРАЦИЯ ЭМБЕДДИНГОВ РЕЗЮМЕ")
    print("=" * 60)

    cur.execute("SELECT id, title, skills FROM resumes")
    resumes = cur.fetchall()
    print(f"\n Найдено резюме: {len(resumes)}\n")

    for i, (resume_id, title, skills_str) in enumerate(resumes, 1):
        print(f"[{i}/{len(resumes)}] Резюме ID={resume_id}: {title}")

        if skills_str:
            skills = [s.strip() for s in skills_str.split(',') if s.strip()]
            skill_embeddings = [model.encode(normalize_skill(s)) for s in skills]

            if skill_embeddings:
                resume_embedding = np.mean(skill_embeddings, axis=0)
            else:
                resume_embedding = model.encode(title)
        else:
            resume_embedding = model.encode(title)

        cur.execute("""
            UPDATE resumes
            SET embedding = %s
            WHERE id = %s
        """, (resume_embedding.tolist(), resume_id))

        print(f"   Эмбеддинг сохранён (размерность: {resume_embedding.shape})\n")

    conn.commit()
    cur.close()
    conn.close()

    print(f" Обработано резюме: {len(resumes)}\n")

def generate_vacancy_embeddings():
    """Генерация эмбеддингов для вакансий"""

    conn = get_db_connection()
    cur = conn.cursor()

    print("=" * 60)
    print("ЭТАП 3: ГЕНЕРАЦИЯ ЭМБЕДДИНГОВ ВАКАНСИЙ")
    print("=" * 60)

    cur.execute("SELECT id, title, requirements FROM vacancies")
    vacancies = cur.fetchall()
    print(f"\n💼 Найдено вакансий: {len(vacancies)}\n")

    for i, (vacancy_id, title, requirements_str) in enumerate(vacancies, 1):
        print(f"[{i}/{len(vacancies)}] Вакансия ID={vacancy_id}: {title}")

        if requirements_str:
            skills = [s.strip() for s in requirements_str.split(',') if s.strip()]
            skill_embeddings = [model.encode(normalize_skill(s)) for s in skills]

            if skill_embeddings:
                vacancy_embedding = np.mean(skill_embeddings, axis=0)
            else:
                vacancy_embedding = model.encode(title)
        else:
            vacancy_embedding = model.encode(title)

        cur.execute("""
            UPDATE vacancies
            SET embedding = %s
            WHERE id = %s
        """, (vacancy_embedding.tolist(), vacancy_id))

        print(f"   Эмбеддинг сохранён (размерность: {vacancy_embedding.shape})\n")

    conn.commit()
    cur.close()
    conn.close()

    print(f" Обработано вакансий: {len(vacancies)}\n")

def test_skill_matching():
    """Тестирование умного сравнения навыков"""

    print("=" * 60)
    print("ТЕСТ: УМНОЕ СРАВНЕНИЕ НАВЫКОВ")
    print("=" * 60)

    test_pairs = [
        ("machine learning", "машинное обучение"),
        ("python", "питон"),
        ("docker", "докер"),
        ("javascript", "джаваскрипт"),
        ("data science", "наука о данных"),
        ("python", "java"),
        ("react", "vue"),
    ]

    print("\n Тестовые пары:\n")

    for skill1, skill2 in test_pairs:
        emb1 = model.encode(skill1)
        emb2 = model.encode(skill2)

        similarity = cosine_similarity([emb1], [emb2])[0][0]
        match = " СОВПАДАЮТ" if similarity >= 0.75 else " РАЗНЫЕ"

        print(f"{skill1:25} ↔ {skill2:25} | {similarity:.2%} | {match}")

    print()

def test_recommendations():
    """Тест системы рекомендаций"""

    conn = get_db_connection()
    cur = conn.cursor()

    print("=" * 60)
    print("ТЕСТ: СИСТЕМА РЕКОМЕНДАЦИЙ")
    print("=" * 60)

    try:
        cur.execute("SELECT id, title, skills FROM resumes LIMIT 1")
        resume = cur.fetchone()

        if not resume:
            print("\n Нет резюме в БД")
            return

        resume_id, title, skills = resume

        print(f"\n Резюме: {title}")
        print(f"   Навыки: {skills or 'Не указаны'}\n")

        cur.execute("""
            SELECT 
                v.id, v.title, v.requirements, v.location,
                v.salary_min, v.salary_max,
                1 - (v.embedding <=> r.embedding) as similarity
            FROM vacancies v, resumes r
            WHERE r.id = %s
            ORDER BY v.embedding <=> r.embedding
            LIMIT 10
        """, (resume_id,))

        results = cur.fetchall()

        if not results:
            print("❌ Не найдено похожих вакансий")
            return

        print(f" Найдено {len(results)} подходящих вакансий:\n")

        for i, (vac_id, vac_title, reqs, loc, sal_min, sal_max, sim) in enumerate(results, 1):
            print(f"{i}. {vac_title}")
            print(f"   Совпадение: {sim * 100:.1f}%")
            if reqs:
                print(f"   Требования: {reqs[:60]}...")
            if loc:
                print(f"   Локация: {loc}")
            if sal_min or sal_max:
                salary = f"{sal_min or 'от'} - {sal_max or 'до'} руб."
                print(f"   Зарплата: {salary}")
            print()

    finally:
        cur.close()
        conn.close()

# ============= ГЛАВНАЯ ФУНКЦИЯ =============

def main():
    """Запуск всех этапов генерации"""

    try:
        generate_skill_embeddings()
        generate_resume_embeddings()
        generate_vacancy_embeddings()

        print("=" * 60)
        print(" ГЕНЕРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 60)

        test_skill_matching()
        test_recommendations()

    except Exception as e:
        print(f"\n Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
