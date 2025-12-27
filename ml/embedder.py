"""Модуль для генерации векторных эмбеддингов резюме и вакансий"""

from sentence_transformers import SentenceTransformer
import numpy as np

# Настройки модели
EMBEDDING_MODEL = "paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DIMENSION = 768


class ResumeVacancyEmbedder:
    """Класс для генерации семантических эмбеддингов"""

    def __init__(self):
        """Инициализация модели BERT для русского и английского языков"""
        print(f"Загрузка модели {EMBEDDING_MODEL}...")
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        print("Модель загружена успешно!")

    def encode_text(self, text: str) -> np.ndarray:
        """
        Генерация эмбеддинга для текста

        Args:
            text: Текст резюме или вакансии

        Returns:
            Вектор размерности 768
        """
        if not text or not text.strip():
            return np.zeros(768)

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding

    def encode_resume(self, resume_data: dict) -> np.ndarray:
        """
        Генерация эмбеддинга для резюме

        Args:
            resume_data: словарь с полями резюме

        Returns:
            Векторное представление резюме
        """
        resume_text = f"""
        Должность: {resume_data.get('title', '')}
        О себе: {resume_data.get('summary', '')}
        Навыки: {resume_data.get('skills', '')}
        Опыт работы: {resume_data.get('experience', '')}
        Образование: {resume_data.get('education', '')}
        """.strip()

        return self.encode_text(resume_text)

    def encode_vacancy(self, vacancy_data: dict) -> np.ndarray:
        """
        Генерация эмбеддинга для вакансии

        Args:
            vacancy_data: словарь с полями вакансии

        Returns:
            Векторное представление вакансии
        """
        vacancy_text = f"""
        Вакансия: {vacancy_data.get('title', '')}
        Описание: {vacancy_data.get('description', '')}
        Требования: {vacancy_data.get('requirements', '')}
        """.strip()

        return self.encode_text(vacancy_text)

    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Вычисление косинусного сходства между двумя эмбеддингами

        Returns:
            Значение от 0 до 1 (чем выше, тем больше похожи)
        """
        from numpy.linalg import norm

        similarity = np.dot(embedding1, embedding2) / (norm(embedding1) * norm(embedding2))
        return float(similarity)


if __name__ == "__main__":
    # Тест модуля
    embedder = ResumeVacancyEmbedder()

    test_resume = {
        'title': 'Python Backend Developer',
        'summary': 'Опытный разработчик с 5 годами коммерческого опыта',
        'skills': 'Python, Django, FastAPI, PostgreSQL, Docker',
        'experience': 'Senior Backend Developer в IT-компании',
        'education': 'ОГУ, Прикладная информатика'
    }

    test_vacancy = {
        'title': 'Senior Python Developer',
        'description': 'Требуется опытный Python-разработчик',
        'requirements': 'Опыт от 3 лет, знание Django или FastAPI, PostgreSQL'
    }

    resume_emb = embedder.encode_resume(test_resume)
    vacancy_emb = embedder.encode_vacancy(test_vacancy)
    similarity = embedder.calculate_similarity(resume_emb, vacancy_emb)

    print(f"Размерность эмбеддинга резюме: {resume_emb.shape}")
    print(f"Размерность эмбеддинга вакансии: {vacancy_emb.shape}")
    print(f"Сходство между резюме и вакансией: {similarity:.3f}")
