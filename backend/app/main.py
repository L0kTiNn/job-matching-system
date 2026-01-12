"""FastAPI приложение для системы подбора вакансий"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Tuple, Set
import sys
import re
from difflib import SequenceMatcher
from collections import Counter

sys.path.append('.')

from backend.app.models import ResumeCreate, VacancyCreate, RecommendationResponse, ResumeUpdate, VacancyUpdate
from backend.app.database import DatabaseManager
from ml.embedder import ResumeVacancyEmbedder

# ============= MULTILINGUAL ЭМБЕДДИНГИ ДЛЯ НАВЫКОВ =============

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from functools import lru_cache

print("🔄 Загрузка multilingual модели для сравнения навыков...")
skill_comparison_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
print("✅ Модель для навыков загружена!")

skill_embeddings_cache = {}

def normalize_skill_text(skill: str) -> str:
    """Нормализация навыка"""
    return skill.lower().strip()

@lru_cache(maxsize=2000)
def get_skill_embedding_cached(skill: str) -> np.ndarray:
    """Получить эмбеддинг навыка с кэшированием"""
    normalized = normalize_skill_text(skill)

    if normalized not in skill_embeddings_cache:
        skill_embeddings_cache[normalized] = skill_comparison_model.encode(normalized)

    return skill_embeddings_cache[normalized]

def are_skills_semantically_similar(skill1: str, skill2: str, threshold: float = 0.75) -> bool:
    """
    Проверка семантической похожести навыков через эмбеддинги
    Работает с русским и английским языками!

    Examples:
        >>> are_skills_semantically_similar("machine learning", "машинное обучение")
        True
        >>> are_skills_semantically_similar("python", "java")
        False
    """
    s1 = normalize_skill_text(skill1)
    s2 = normalize_skill_text(skill2)

    # Быстрая проверка точного совпадения
    if s1 == s2:
        return True

    # Сравнение через эмбеддинги
    try:
        emb1 = get_skill_embedding_cached(skill1)
        emb2 = get_skill_embedding_cached(skill2)

        similarity = cosine_similarity([emb1], [emb2])[0][0]
        return similarity >= threshold
    except Exception as e:
        print(f"Ошибка сравнения навыков '{skill1}' и '{skill2}': {e}")
        return False

# ============= КОНЕЦ ЭМБЕДДИНГОВ =============

app = FastAPI(
    title="Job Matching System API",
    description="Система подбора вакансий с использованием ML",
    version="2.0.0"
)

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация ML-модели (один раз при запуске)
embedder = ResumeVacancyEmbedder()


# ============= УМНОЕ ИЗВЛЕЧЕНИЕ НАВЫКОВ (NLP) =============

class SkillExtractor:
    """Продвинутый экстрактор навыков с нормализацией и контекстным анализом"""

    # База данных технических навыков с синонимами
    SKILL_DATABASE = {
        # Языки программирования
        "python": ["python", "python3", "py"],
        "javascript": ["javascript", "js", "ecmascript"],
        "typescript": ["typescript", "ts"],
        "java": ["java", "java se", "java ee"],
        "c++": ["c++", "cpp", "c plus plus"],
        "c#": ["c#", "csharp", "c sharp"],
        "php": ["php", "php7", "php8"],
        "ruby": ["ruby", "ruby on rails", "ror"],
        "go": ["go", "golang"],
        "rust": ["rust"],
        "kotlin": ["kotlin"],
        "swift": ["swift"],
        "scala": ["scala"],
        "r": ["r", "rstudio"],
        "perl": ["perl"],

        # Frontend
        "react": ["react", "reactjs", "react.js", "react js"],
        "vue": ["vue", "vuejs", "vue.js", "vue js"],
        "angular": ["angular", "angularjs"],
        "html": ["html", "html5"],
        "css": ["css", "css3"],
        "sass": ["sass", "scss"],
        "less": ["less"],
        "webpack": ["webpack"],
        "redux": ["redux"],
        "next.js": ["next", "nextjs", "next.js"],
        "nuxt": ["nuxt", "nuxtjs"],
        "tailwind": ["tailwind", "tailwindcss"],
        "bootstrap": ["bootstrap"],
        "jquery": ["jquery"],

        # Backend
        "fastapi": ["fastapi", "fast api"],
        "django": ["django"],
        "flask": ["flask"],
        "express": ["express", "expressjs", "express.js"],
        "node.js": ["node", "nodejs", "node.js"],
        "spring": ["spring", "spring boot"],
        "laravel": ["laravel"],
        "asp.net": ["asp.net", "asp", ".net"],
        "rails": ["rails", "ruby on rails"],
        "nest.js": ["nest", "nestjs"],

        # Базы данных
        "postgresql": ["postgresql", "postgres", "psql"],
        "mysql": ["mysql"],
        "mongodb": ["mongodb", "mongo"],
        "redis": ["redis"],
        "elasticsearch": ["elasticsearch", "elastic"],
        "cassandra": ["cassandra"],
        "oracle": ["oracle", "oracle db"],
        "mssql": ["mssql", "sql server"],
        "sqlite": ["sqlite"],
        "dynamodb": ["dynamodb"],
        "mariadb": ["mariadb"],

        # DevOps & Cloud
        "docker": ["docker"],
        "kubernetes": ["kubernetes", "k8s"],
        "jenkins": ["jenkins"],
        "gitlab": ["gitlab", "gitlab ci"],
        "github": ["github", "github actions"],
        "aws": ["aws", "amazon web services"],
        "azure": ["azure", "microsoft azure"],
        "gcp": ["gcp", "google cloud"],
        "terraform": ["terraform"],
        "ansible": ["ansible"],

        # Инструменты
        "git": ["git"],
        "linux": ["linux", "unix"],
        "nginx": ["nginx"],
        "apache": ["apache"],
        "rabbitmq": ["rabbitmq", "rabbit mq"],
        "kafka": ["kafka", "apache kafka"],

        # API
        "rest": ["rest", "restful", "rest api"],
        "graphql": ["graphql", "graph ql"],
        "grpc": ["grpc"],
        "websocket": ["websocket", "websockets"],

        # Тестирование
        "pytest": ["pytest"],
        "unittest": ["unittest"],
        "jest": ["jest"],
        "selenium": ["selenium"],
        "cypress": ["cypress"],

        # ML/Data
        "machine learning": ["machine learning", "ml", "машинное обучение", "машин обучение", "машинное обуч"],
        "deep learning": ["deep learning", "dl", "глубокое обучение", "глубинное обучение"],
        "tensorflow": ["tensorflow", "tf", "тенсорфлоу"],
        "pytorch": ["pytorch", "пайторч"],
        "scikit-learn": ["scikit-learn", "sklearn", "сайкит", "сайкит-лёрн"],
        "pandas": ["pandas", "пандас"],
        "numpy": ["numpy", "нампай"],
        "jupyter": ["jupyter", "jupyter notebook", "джупитер"],
        "data science": ["data science", "наука о данных", "дата сайенс"],
        "data analysis": ["data analysis", "анализ данных"],
        "big data": ["big data", "большие данные", "биг дата"],

        # Soft skills
        "agile": ["agile", "scrum", "kanban"],
        "английский": ["английский", "english", "english language"],
        "коммуникация": ["коммуникация", "communication"],
        "лидерство": ["лидерство", "leadership"],
        "командная работа": ["командная работа", "teamwork", "team work"],
    }

    # Обратный индекс для быстрого поиска
    SYNONYM_MAP = {}
    for canonical, synonyms in SKILL_DATABASE.items():
        for syn in synonyms:
            SYNONYM_MAP[syn.lower()] = canonical

    @classmethod
    def extract_skills(cls, text: str) -> Set[str]:
        """
        Умное извлечение навыков с нормализацией

        Args:
            text: Текст резюме или вакансии

        Returns:
            Множество нормализованных навыков
        """
        if not text:
            return set()

        text_lower = text.lower()
        found_skills = set()

        # 1. Точное совпадение по синонимам
        for synonym, canonical in cls.SYNONYM_MAP.items():
            # Используем границы слов для точности
            pattern = r'\b' + re.escape(synonym) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(canonical)

        # 2. Fuzzy matching для опечаток (только для длинных слов)
        words = re.findall(r'\b\w{4,}\b', text_lower)
        for word in words:
            best_match = cls._fuzzy_match_skill(word)
            if best_match:
                found_skills.add(best_match)

        return found_skills

    @classmethod
    def _fuzzy_match_skill(cls, word: str, threshold: float = 0.85) -> str:
        """
        Нечеткое сопоставление для учета опечаток

        Args:
            word: Слово для проверки
            threshold: Порог сходства (0-1)

        Returns:
            Канонический навык или None
        """
        best_score = 0
        best_skill = None

        for synonym, canonical in cls.SYNONYM_MAP.items():
            # Пропускаем короткие синонимы для fuzzy matching
            if len(synonym) < 4:
                continue

            similarity = SequenceMatcher(None, word, synonym).ratio()
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_skill = canonical

        return best_skill

    @classmethod
    def categorize_skills(cls, skills: Set[str]) -> Dict[str, List[str]]:
        """Категоризация навыков"""
        categories = {
            "languages": [],
            "frontend": [],
            "backend": [],
            "databases": [],
            "devops": [],
            "tools": [],
            "ml": [],
            "soft_skills": []
        }

        category_map = {
            "python": "languages", "javascript": "languages", "java": "languages",
            "typescript": "languages", "c++": "languages", "c#": "languages",

            "react": "frontend", "vue": "frontend", "angular": "frontend",
            "html": "frontend", "css": "frontend",

            "django": "backend", "flask": "backend", "fastapi": "backend",
            "express": "backend", "node.js": "backend",

            "postgresql": "databases", "mysql": "databases", "mongodb": "databases",
            "redis": "databases",

            "docker": "devops", "kubernetes": "devops", "aws": "devops",
            "azure": "devops", "jenkins": "devops",

            "git": "tools", "linux": "tools", "nginx": "tools",

            "machine learning": "ml", "tensorflow": "ml", "pytorch": "ml",
            "pandas": "ml",

            "agile": "soft_skills", "английский": "soft_skills",
            "коммуникация": "soft_skills", "лидерство": "soft_skills"
        }

        for skill in skills:
            category = category_map.get(skill, "tools")
            categories[category].append(skill)

        # Удаляем пустые категории
        return {k: sorted(v) for k, v in categories.items() if v}


# ============= ПРОДВИНУТАЯ СИСТЕМА SCORING =============

class MatchAnalyzer:
    """Многофакторный анализ совместимости резюме и вакансии"""

    @staticmethod
    def calculate_match_score(
        resume_skills: Set[str],
        vacancy_skills: Set[str],
        resume_text: str,
        vacancy_text: str
    ) -> Dict:
        """
        Рассчитывает многофакторную оценку совпадения
        НОВОЕ: Использует семантическое сравнение через эмбеддинги!
        """

        # 🚀 УМНОЕ сравнение с учётом синонимов и переводов!
        matched_skills = []
        missing_skills = []
        used_resume_skills = set()

        # Для каждого требуемого навыка ищем совпадение в резюме
        for vacancy_skill in vacancy_skills:
            found = False

            for resume_skill in resume_skills:
                if resume_skill in used_resume_skills:
                    continue

                # ПРОВЕРКА через эмбеддинги (русский + английский!)
                if are_skills_semantically_similar(vacancy_skill, resume_skill):
                    matched_skills.append(vacancy_skill)
                    used_resume_skills.add(resume_skill)
                    found = True
                    break

            if not found:
                missing_skills.append(vacancy_skill)

        # Дополнительные навыки
        extra_skills = [s for s in resume_skills if s not in used_resume_skills]

        # 1. Базовая оценка по навыкам
        if vacancy_skills:
            skills_score = (len(matched_skills) / len(vacancy_skills)) * 100
        else:
            skills_score = 0

        # 2. Бонус за дополнительные навыки
        extra_bonus = min(len(extra_skills) * 2, 15)

        # 3. Штраф за критичные пропущенные навыки
        critical_missing = MatchAnalyzer._identify_critical_skills(set(missing_skills))
        critical_penalty = len(critical_missing) * 10

        # 4. Итоговая оценка
        total_score = min(max(skills_score + extra_bonus - critical_penalty, 0), 100)

        return {
            "total_score": round(total_score, 1),
            "skills_score": round(skills_score, 1),
            "matched_skills": sorted(matched_skills),
            "missing_skills": sorted(missing_skills),
            "critical_missing": sorted(list(critical_missing)),
            "extra_skills": sorted(extra_skills),
            "extra_bonus": extra_bonus,
            "critical_penalty": critical_penalty
        }

    @staticmethod
    def _identify_critical_skills(missing: Set[str]) -> Set[str]:
        """Определяет критически важные пропущенные навыки"""
        critical_keywords = {
            "python", "javascript", "java", "react", "vue", "angular",
            "postgresql", "mysql", "mongodb", "docker", "kubernetes",
            "aws", "azure", "английский"
        }
        return missing & critical_keywords


# ============= ГЕНЕРАТОР УМНЫХ РЕКОМЕНДАЦИЙ =============

class RecommendationEngine:
    """Генератор персонализированных рекомендаций"""

    @staticmethod
    def generate_recommendations(analysis: Dict) -> str:
        """Генерирует детальные рекомендации на основе анализа"""

        score = analysis["total_score"]
        matched = analysis["matched_skills"]
        missing = analysis["missing_skills"]
        critical = analysis["critical_missing"]
        extra = analysis["extra_skills"]

        # 1. Отличное совпадение (90%+)
        if score >= 90:
            return (
                f"🎉 **Отличное совпадение!** Ваше резюме на {round(score)}% соответствует требованиям.\n\n"
                f"✅ Совпало навыков: {len(matched)}\n"
                f"💡 У вас есть {len(extra)} дополнительных навыков, что выделяет вас среди других кандидатов!\n\n"
                f"**Рекомендация:** Смело откликайтесь! Высокие шансы на приглашение."
            )

        # 2. Хорошее совпадение (70-89%)
        elif score >= 70:
            tips = []
            if missing:
                top_missing = missing[:3]
                tips.append(f"Добавьте в резюме: {', '.join(top_missing)}")
            if critical:
                tips.append(f"⚠️ Критично изучить: {', '.join(critical)}")

            recommendations_text = "\n".join([f"• {tip}" for tip in tips])

            return (
                f"✅ **Хорошее совпадение!** Ваше резюме на {round(score)}% соответствует требованиям.\n\n"
                f"Совпало {len(matched)} из {len(matched) + len(missing)} требуемых навыков.\n\n"
                f"**Как улучшить резюме:**\n{recommendations_text}\n\n"
                f"Это повысит ваши шансы на приглашение до ~95%!"
            )

        # 3. Среднее совпадение (50-69%)
        elif score >= 50:
            if critical:
                return (
                    f"💡 **Среднее совпадение** ({round(score)}%). У вас есть потенциал!\n\n"
                    f"✅ Совпало: {len(matched)} навыков\n"
                    f"❌ Не хватает: {len(missing)} навыков\n\n"
                    f"**⚠️ Критично важно изучить:**\n"
                    + "\n".join([f"• {skill}" for skill in critical[:5]]) +
                    f"\n\n**Рекомендация:** Пройдите курсы по этим технологиям и обновите резюме через 1-2 месяца."
                )
            else:
                return (
                    f"💡 **Среднее совпадение** ({round(score)}%). Можно улучшить!\n\n"
                    f"**Добавьте в резюме навыки:**\n"
                    + "\n".join([f"• {skill}" for skill in missing[:5]]) +
                    f"\n\nЭто повысит совпадение до ~{min(round(score) + 20, 95)}%!"
                )

        # 4. Низкое совпадение (<50%)
        else:
            return (
                f"⚠️ **Низкое совпадение** ({round(score)}%). Эта вакансия может быть сложной.\n\n"
                f"Не хватает {len(missing)} ключевых навыков из {len(missing) + len(matched)}.\n\n"
                f"**Критичные навыки для изучения:**\n"
                + "\n".join([f"• {skill}" for skill in (critical or missing)[:7]]) +
                f"\n\n**Рекомендация:** Рассмотрите вакансии, более подходящие под ваш текущий опыт, "
                f"или инвестируйте время в изучение недостающих технологий."
            )


# ============= ENDPOINTS =============

@app.get("/")
def root():
    """Корневой endpoint"""
    return {
        "message": "Job Matching System API",
        "version": "2.0.0",
        "endpoints": {
            "docs": "/docs",
            "resumes": "/api/resumes",
            "vacancies": "/api/vacancies",
            "recommendations": "/api/resumes/{id}/recommendations"
        }
    }


@app.get("/health")
def health_check():
    """Проверка работоспособности"""
    return {"status": "healthy"}


@app.post("/api/resumes", status_code=201)
def create_resume(resume: ResumeCreate):
    """Создание нового резюме"""
    db = DatabaseManager()

    try:
        db.connect()

        query = """
        INSERT INTO resumes (user_id, title, summary, skills, experience, education, 
                           desired_position, desired_salary, location)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """

        db.cursor.execute(query, (
            resume.user_id, resume.title, resume.summary, resume.skills,
            resume.experience, resume.education, resume.desired_position,
            resume.desired_salary, resume.location
        ))

        resume_id = db.cursor.fetchone()[0]
        db.conn.commit()

        embedding = embedder.encode_resume(resume.dict())
        db.save_resume_embedding(resume_id, embedding)

        return {
            "id": resume_id,
            "message": "Резюме создано успешно",
            "embedding_generated": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post("/api/vacancies", status_code=201)
def create_vacancy(vacancy: VacancyCreate):
    """Создание новой вакансии"""
    db = DatabaseManager()

    try:
        db.connect()

        query = """
        INSERT INTO vacancies (employer_id, title, description, requirements,
                             salary_min, salary_max, location)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """

        db.cursor.execute(query, (
            vacancy.employer_id, vacancy.title, vacancy.description,
            vacancy.requirements, vacancy.salary_min, vacancy.salary_max,
            vacancy.location
        ))

        vacancy_id = db.cursor.fetchone()[0]
        db.conn.commit()

        embedding = embedder.encode_vacancy(vacancy.dict())
        db.save_vacancy_embedding(vacancy_id, embedding)

        return {
            "id": vacancy_id,
            "message": "Вакансия создана успешно",
            "embedding_generated": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/resumes/{resume_id}/recommendations")
def get_vacancy_recommendations(resume_id: int, limit: int = 10):
    """Получить рекомендации вакансий для резюме"""
    db = DatabaseManager()

    try:
        db.connect()

        db.cursor.execute("SELECT id FROM resumes WHERE id = %s", (resume_id,))
        if not db.cursor.fetchone():
            raise HTTPException(status_code=404, detail="Резюме не найдено")

        similar = db.find_similar_vacancies(resume_id, limit)

        if not similar:
            return {
                "resume_id": resume_id,
                "recommendations": [],
                "message": "Подходящие вакансии не найдены"
            }

        recommendations = []
        for vacancy_id, title, description, salary_min, salary_max, location, similarity in similar:
            recommendations.append({
                "id": vacancy_id,
                "title": title,
                "description": description[:200] + "..." if description and len(description) > 200 else description,
                "similarity": round(similarity * 100, 2),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "location": location
            })

        return {
            "resume_id": resume_id,
            "recommendations": recommendations,
            "total": len(recommendations)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/vacancies/{vacancy_id}/candidates")
def get_resume_recommendations(vacancy_id: int, limit: int = 10):
    """
    🚀 ПОЛНОСТЬЮ ПЕРЕРАБОТАНО!
    Использует SkillExtractor для подсчёта процента (как для вакансий!)
    """
    db = DatabaseManager()

    try:
        db.connect()

        # Получаем вакансию
        db.cursor.execute("""
            SELECT id, title, description, requirements, salary_min, salary_max, location
            FROM vacancies WHERE id = %s
        """, (vacancy_id,))

        vacancy_data = db.cursor.fetchone()
        if not vacancy_data:
            raise HTTPException(status_code=404, detail="Вакансия не найдена")

        # Формируем текст вакансии для анализа
        vacancy_text = " ".join(filter(None, [
            vacancy_data[1],  # title
            vacancy_data[2],  # description
            vacancy_data[3]   # requirements
        ]))

        # Извлекаем навыки вакансии
        vacancy_skills = SkillExtractor.extract_skills(vacancy_text)

        print(f"🔍 Навыки вакансии: {vacancy_skills}")

        # Получаем ВСЕ активные резюме
        db.cursor.execute("""
            SELECT id, title, summary, skills, experience, education, 
                   desired_position, desired_salary, location
            FROM resumes
            WHERE is_active = true
            ORDER BY created_at DESC
        """)

        all_resumes = db.cursor.fetchall()

        # Анализируем КАЖДОЕ резюме через SkillExtractor
        candidates = []

        for resume_row in all_resumes:
            resume_id, title, summary, skills, experience, education, desired_position, desired_salary, location = resume_row

            # Формируем текст резюме
            resume_text = " ".join(filter(None, [
                title, summary, skills, experience, education, desired_position
            ]))

            # Извлекаем навыки резюме
            resume_skills = SkillExtractor.extract_skills(resume_text)

            # 🔥 СЧИТАЕМ СОВПАДЕНИЕ ЧЕРЕЗ SkillExtractor!
            analysis = MatchAnalyzer.calculate_match_score(
                resume_skills,
                vacancy_skills,
                resume_text,
                vacancy_text
            )

            match_percentage = analysis["total_score"]

            # Добавляем в список если есть хоть какое-то совпадение
            if match_percentage > 0:
                candidates.append({
                    "resume_id": resume_id,
                    "full_name": f"Кандидат #{resume_id}",
                    "title": title or "Без названия",
                    "desired_position": desired_position or "Не указана",
                    "skills": skills or "Не указаны",
                    "experience": experience or "Не указан",
                    "education": education or "Не указано",
                    "contact_email": "candidate@example.com",
                    "contact_phone": "+7 (XXX) XXX-XX-XX",
                    "match_percentage": round(match_percentage, 1),  # 🔥 ИЗ SkillExtractor!
                    "desired_salary": desired_salary,
                    "location": location or "Не указана"
                })

        # Сортируем по убыванию процента совпадения
        candidates.sort(key=lambda x: x["match_percentage"], reverse=True)

        # Ограничиваем количество результатов
        candidates = candidates[:limit]

        print(f"✅ Найдено кандидатов: {len(candidates)}")

        return {
            "vacancy": {
                "id": vacancy_data[0],
                "title": vacancy_data[1],
                "description": vacancy_data[2]
            },
            "candidates": candidates,
            "total": len(candidates)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка в get_resume_recommendations: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/vacancies/all")
def get_all_vacancies():
    """Получить все вакансии"""
    db = DatabaseManager()

    try:
        db.connect()
        db.cursor.execute("""
            SELECT id, title, description, salary_min, salary_max, location
            FROM vacancies
            ORDER BY created_at DESC
        """)

        vacancies = []
        for row in db.cursor.fetchall():
            vacancies.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "salary_min": row[3],
                "salary_max": row[4],
                "location": row[5]
            })

        return vacancies

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.delete("/api/vacancies/{vacancy_id}")
def delete_vacancy(vacancy_id: int):
    """Удалить вакансию"""
    db = DatabaseManager()

    try:
        db.connect()

        db.cursor.execute("SELECT id FROM vacancies WHERE id = %s", (vacancy_id,))
        if not db.cursor.fetchone():
            raise HTTPException(status_code=404, detail="Вакансия не найдена")

        db.cursor.execute("DELETE FROM vacancies WHERE id = %s", (vacancy_id,))
        db.conn.commit()

        return {
            "message": f"Вакансия {vacancy_id} успешно удалена",
            "deleted_id": vacancy_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.delete("/api/resumes/{resume_id}")
def delete_resume(resume_id: int):
    """Удалить резюме"""
    db = DatabaseManager()

    try:
        db.connect()

        db.cursor.execute("SELECT id FROM resumes WHERE id = %s", (resume_id,))
        if not db.cursor.fetchone():
            raise HTTPException(status_code=404, detail="Резюме не найдено")

        db.cursor.execute("DELETE FROM resumes WHERE id = %s", (resume_id,))
        db.conn.commit()

        return {
            "message": f"Резюме {resume_id} успешно удалено",
            "deleted_id": resume_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/resumes/all")
def get_all_resumes():
    """Получить все резюме"""
    db = DatabaseManager()

    try:
        db.connect()
        db.cursor.execute("""
            SELECT id, title, summary, skills, desired_salary, location
            FROM resumes
            ORDER BY created_at DESC
        """)

        resumes = []
        for row in db.cursor.fetchall():
            resumes.append({
                "id": row[0],
                "title": row[1],
                "summary": row[2],
                "skills": row[3],
                "desired_salary": row[4],
                "location": row[5]
            })

        return resumes

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/resumes/{resume_id}")
def get_resume(resume_id: int):
    """Получить одно резюме по ID"""
    db = DatabaseManager()

    try:
        db.connect()

        db.cursor.execute("""
            SELECT id, user_id, title, summary, skills, experience, education,
                   desired_position, desired_salary, location, created_at
            FROM resumes
            WHERE id = %s
        """, (resume_id,))

        row = db.cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Резюме не найдено")

        return {
            "id": row[0],
            "user_id": row[1],
            "title": row[2],
            "summary": row[3],
            "skills": row[4],
            "experience": row[5],
            "education": row[6],
            "desired_position": row[7],
            "desired_salary": row[8],
            "location": row[9],
            "created_at": str(row[10]) if row[10] else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.put("/api/resumes/{resume_id}")
def update_resume(resume_id: int, resume: ResumeUpdate):
    """Обновить резюме"""
    db = DatabaseManager()

    try:
        db.connect()

        db.cursor.execute("SELECT id FROM resumes WHERE id = %s", (resume_id,))
        if not db.cursor.fetchone():
            raise HTTPException(status_code=404, detail="Резюме не найдено")

        update_fields = []
        values = []

        for field, value in resume.dict(exclude_unset=True).items():
            update_fields.append(f"{field} = %s")
            values.append(value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")

        values.append(resume_id)

        query = f"""
            UPDATE resumes 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """

        db.cursor.execute(query, values)
        db.conn.commit()

        db.cursor.execute("""
            SELECT title, summary, skills, experience, education, 
                   desired_position, desired_salary, location
            FROM resumes WHERE id = %s
        """, (resume_id,))

        row = db.cursor.fetchone()
        resume_data = {
            'title': row[0],
            'summary': row[1],
            'skills': row[2],
            'experience': row[3],
            'education': row[4],
            'desired_position': row[5],
            'desired_salary': row[6],
            'location': row[7]
        }

        embedding = embedder.encode_resume(resume_data)
        db.save_resume_embedding(resume_id, embedding)

        return {
            "message": "Резюме успешно обновлено",
            "id": resume_id,
            "embedding_updated": True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/vacancies/{vacancy_id}")
def get_vacancy(vacancy_id: int):
    """Получить одну вакансию по ID"""
    db = DatabaseManager()

    try:
        db.connect()

        db.cursor.execute("""
            SELECT id, employer_id, title, description, requirements,
                   salary_min, salary_max, location, created_at
            FROM vacancies
            WHERE id = %s
        """, (vacancy_id,))

        row = db.cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Вакансия не найдена")

        return {
            "id": row[0],
            "employer_id": row[1],
            "title": row[2],
            "description": row[3],
            "requirements": row[4],
            "salary_min": row[5],
            "salary_max": row[6],
            "location": row[7],
            "created_at": str(row[8]) if row[8] else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.put("/api/vacancies/{vacancy_id}")
def update_vacancy(vacancy_id: int, vacancy: VacancyUpdate):
    """Обновить вакансию"""
    db = DatabaseManager()

    try:
        db.connect()

        db.cursor.execute("SELECT id FROM vacancies WHERE id = %s", (vacancy_id,))
        if not db.cursor.fetchone():
            raise HTTPException(status_code=404, detail="Вакансия не найдена")

        update_fields = []
        values = []

        for field, value in vacancy.dict(exclude_unset=True).items():
            update_fields.append(f"{field} = %s")
            values.append(value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")

        values.append(vacancy_id)

        query = f"""
            UPDATE vacancies 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """

        db.cursor.execute(query, values)
        db.conn.commit()

        db.cursor.execute("""
            SELECT title, description, requirements, salary_min, salary_max, location
            FROM vacancies WHERE id = %s
        """, (vacancy_id,))

        row = db.cursor.fetchone()
        vacancy_data = {
            'title': row[0],
            'description': row[1],
            'requirements': row[2],
            'salary_min': row[3],
            'salary_max': row[4],
            'location': row[5]
        }

        embedding = embedder.encode_vacancy(vacancy_data)
        db.save_vacancy_embedding(vacancy_id, embedding)

        return {
            "message": "Вакансия успешно обновлена",
            "id": vacancy_id,
            "embedding_updated": True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/resumes/{resume_id}/vacancies/{vacancy_id}/match-analysis")
def analyze_match(resume_id: int, vacancy_id: int):
    """
    🚀 УЛУЧШЕННЫЙ детальный анализ совпадения резюме и вакансии
    Использует multilingual эмбеддинги для сравнения навыков!
    """
    db = DatabaseManager()

    try:
        db.connect()

        db.cursor.execute("""
            SELECT title, summary, skills, experience, education, desired_position
            FROM resumes WHERE id = %s
        """, (resume_id,))

        resume_data = db.cursor.fetchone()
        if not resume_data:
            raise HTTPException(status_code=404, detail="Резюме не найдено")

        db.cursor.execute("""
            SELECT title, description, requirements, salary_min, salary_max, location
            FROM vacancies WHERE id = %s
        """, (vacancy_id,))

        vacancy_data = db.cursor.fetchone()
        if not vacancy_data:
            raise HTTPException(status_code=404, detail="Вакансия не найдена")

        resume_text = " ".join(filter(None, [
            resume_data[0], resume_data[1], resume_data[2],
            resume_data[3], resume_data[4], resume_data[5]
        ]))

        vacancy_text = " ".join(filter(None, [
            vacancy_data[0], vacancy_data[1], vacancy_data[2]
        ]))

        resume_skills = SkillExtractor.extract_skills(resume_text)
        vacancy_skills = SkillExtractor.extract_skills(vacancy_text)

        analysis = MatchAnalyzer.calculate_match_score(
            resume_skills, vacancy_skills, resume_text, vacancy_text
        )

        recommendations = RecommendationEngine.generate_recommendations(analysis)

        salary_text = "Не указана"
        if vacancy_data[3] and vacancy_data[4]:
            salary_text = f"{vacancy_data[3]:,} - {vacancy_data[4]:,} ₽"
        elif vacancy_data[3]:
            salary_text = f"от {vacancy_data[3]:,} ₽"
        elif vacancy_data[4]:
            salary_text = f"до {vacancy_data[4]:,} ₽"

        return {
            "resume_id": resume_id,
            "vacancy_id": vacancy_id,
            "vacancy_title": vacancy_data[0],
            "vacancy_description": vacancy_data[1],
            "vacancy_salary": salary_text,
            "vacancy_location": vacancy_data[5] or "Не указана",
            "match_percentage": analysis["total_score"],
            "skills_match_percentage": analysis["skills_score"],
            "matched_skills": analysis["matched_skills"],
            "missing_skills": analysis["missing_skills"],
            "critical_missing_skills": analysis["critical_missing"],
            "extra_skills": analysis["extra_skills"],
            "extra_skills_bonus": analysis["extra_bonus"],
            "critical_penalty": analysis["critical_penalty"],
            "recommendations": recommendations,
            "stats": {
                "total_resume_skills": len(resume_skills),
                "total_vacancy_skills": len(vacancy_skills),
                "matched_count": len(analysis["matched_skills"]),
                "missing_count": len(analysis["missing_skills"]),
                "extra_count": len(analysis["extra_skills"])
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка в analyze_match: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/vacancies/{vacancy_id}/resumes/{resume_id}/match-analysis")
def analyze_candidate_match(vacancy_id: int, resume_id: int):
    """
    🚀 ЗЕРКАЛЬНЫЙ анализ: Вакансия → Резюме (для работодателя)
    Использует ту же логику что и анализ резюме → вакансия
    """
    return analyze_match(resume_id, vacancy_id)


@app.get("/api/skills/extract")
def extract_skills_from_text(text: str):
    """Endpoint для тестирования извлечения навыков"""
    skills = SkillExtractor.extract_skills(text)
    categories = SkillExtractor.categorize_skills(skills)

    return {
        "text": text,
        "extracted_skills": sorted(list(skills)),
        "total_count": len(skills),
        "categorized": categories
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
