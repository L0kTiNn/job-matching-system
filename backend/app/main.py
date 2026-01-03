"""FastAPI приложение для системы подбора вакансий"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import sys

sys.path.append('.')

from backend.app.models import ResumeCreate, VacancyCreate, RecommendationResponse, ResumeUpdate, VacancyUpdate
from backend.app.database import DatabaseManager
from ml.embedder import ResumeVacancyEmbedder


app = FastAPI(
    title="Job Matching System API",
    description="Система подбора вакансий с использованием ML",
    version="1.0.0"
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


@app.get("/")
def root():
    """Корневой endpoint"""
    return {
        "message": "Job Matching System API",
        "version": "1.0.0",
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

        # Вставка резюме в БД
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

        # Генерация эмбеддинга
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

        # Вставка вакансии в БД
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

        # Генерация эмбеддинга
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

        # Проверка существования резюме
        db.cursor.execute("SELECT id FROM resumes WHERE id = %s", (resume_id,))
        if not db.cursor.fetchone():
            raise HTTPException(status_code=404, detail="Резюме не найдено")

        # Поиск похожих вакансий
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
    """Получить рекомендации кандидатов для вакансии"""
    db = DatabaseManager()

    try:
        db.connect()

        # Проверка существования вакансии
        db.cursor.execute("SELECT id FROM vacancies WHERE id = %s", (vacancy_id,))
        if not db.cursor.fetchone():
            raise HTTPException(status_code=404, detail="Вакансия не найдена")

        # Поиск подходящих резюме
        similar = db.find_similar_resumes(vacancy_id, limit)

        candidates = []
        for resume_id, title, summary, skills, salary, location, similarity in similar:
            candidates.append({
                "id": resume_id,
                "title": title,
                "summary": summary[:200] + "..." if summary and len(summary) > 200 else summary,
                "skills": skills,
                "similarity": round(similarity * 100, 2),
                "desired_salary": salary,
                "location": location
            })

        return {
            "vacancy_id": vacancy_id,
            "candidates": candidates,
            "total": len(candidates)
        }

    except HTTPException:
        raise
    except Exception as e:
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

        # Проверка существования
        db.cursor.execute("SELECT id FROM vacancies WHERE id = %s", (vacancy_id,))
        if not db.cursor.fetchone():
            raise HTTPException(status_code=404, detail="Вакансия не найдена")

        # Удаление
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

        # Проверка существования
        db.cursor.execute("SELECT id FROM resumes WHERE id = %s", (resume_id,))
        if not db.cursor.fetchone():
            raise HTTPException(status_code=404, detail="Резюме не найдено")

        # Удаление
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

        # Получение резюме
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

        # Проверка существования
        db.cursor.execute("SELECT id FROM resumes WHERE id = %s", (resume_id,))
        if not db.cursor.fetchone():
            raise HTTPException(status_code=404, detail="Резюме не найдено")

        # Обновление только переданных полей
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

        # Регенерация эмбеддинга после обновления
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

        # Получение вакансии
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

        # Проверка существования
        db.cursor.execute("SELECT id FROM vacancies WHERE id = %s", (vacancy_id,))
        if not db.cursor.fetchone():
            raise HTTPException(status_code=404, detail="Вакансия не найдена")

        # Обновление только переданных полей
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

        # Регенерация эмбеддинга после обновления
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
