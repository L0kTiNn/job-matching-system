"""Конфигурация для ML-модуля"""

# Настройки модели для генерации эмбеддингов
EMBEDDING_MODEL = "paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DIMENSION = 768

# Настройки подключения к БД
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "job_matching_system",
    "user": "postgres",
    "password": "diploma2025"
}
