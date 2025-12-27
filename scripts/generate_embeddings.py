"""Скрипт для генерации эмбеддингов для всех резюме и вакансий в БД"""

import sys

sys.path.append('.')  # Добавляем корень проекта в путь

from ml.embedder import ResumeVacancyEmbedder
from backend.app.database import DatabaseManager


def generate_all_embeddings():
    """Генерация эмбеддингов для всех резюме и вакансий"""

    print("=" * 60)
    print("ГЕНЕРАЦИЯ ВЕКТОРНЫХ ЭМБЕДДИНГОВ")
    print("=" * 60)

    # Инициализация
    embedder = ResumeVacancyEmbedder()
    db = DatabaseManager()

    try:
        db.connect()

        # === ОБРАБОТКА РЕЗЮМЕ ===
        print("\n📄 Обработка резюме...")
        resumes = db.get_all_resumes()
        print(f"Найдено резюме: {len(resumes)}")

        for i, resume in enumerate(resumes, 1):
            print(f"\n[{i}/{len(resumes)}] Обработка резюме ID={resume['id']}: {resume['title']}")

            # Генерация эмбеддинга
            embedding = embedder.encode_resume(resume)

            # Сохранение в БД
            db.save_resume_embedding(resume['id'], embedding)

            print(f"  ✅ Эмбеддинг сохранён (размерность: {embedding.shape})")

        print(f"\n✅ Обработано резюме: {len(resumes)}")

        # === ОБРАБОТКА ВАКАНСИЙ ===
        print("\n💼 Обработка вакансий...")
        vacancies = db.get_all_vacancies()
        print(f"Найдено вакансий: {len(vacancies)}")

        for i, vacancy in enumerate(vacancies, 1):
            print(f"\n[{i}/{len(vacancies)}] Обработка вакансии ID={vacancy['id']}: {vacancy['title']}")

            # Генерация эмбеддинга
            embedding = embedder.encode_vacancy(vacancy)

            # Сохранение в БД
            db.save_vacancy_embedding(vacancy['id'], embedding)

            print(f"  ✅ Эмбеддинг сохранён (размерность: {embedding.shape})")

        print(f"\n✅ Обработано вакансий: {len(vacancies)}")

        print("\n" + "=" * 60)
        print("ГЕНЕРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_recommendations():
    """Тест системы рекомендаций"""

    print("\n" + "=" * 60)
    print("ТЕСТ СИСТЕМЫ РЕКОМЕНДАЦИЙ")
    print("=" * 60)

    db = DatabaseManager()

    try:
        db.connect()

        # Получаем первое резюме
        resumes = db.get_all_resumes()
        if not resumes:
            print("❌ Нет резюме в БД")
            return

        resume = resumes[0]
        print(f"\n📄 Резюме: {resume['title']}")
        print(f"   Навыки: {resume.get('skills', 'Не указаны')}")

        # Ищем похожие вакансии
        print(f"\n🔍 Поиск подходящих вакансий...\n")
        similar = db.find_similar_vacancies(resume['id'], limit=10)

        if not similar:
            print("❌ Не найдено похожих вакансий (возможно, не сгенерированы эмбеддинги)")
            return

        print(f"Найдено {len(similar)} подходящих вакансий:\n")

        for i, (vacancy_id, title, description, salary_min, salary_max, location, similarity) in enumerate(similar, 1):
            print(f"{i}. {title}")
            print(f"   Сходство: {similarity * 100:.1f}%")
            if salary_min or salary_max:
                salary_str = f"{salary_min or 'от'} - {salary_max or 'до'} руб."
                print(f"   Зарплата: {salary_str}")
            if location:
                print(f"   Локация: {location}")
            print()

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    # Генерация эмбеддингов
    generate_all_embeddings()

    # Тест рекомендаций
    test_recommendations()
