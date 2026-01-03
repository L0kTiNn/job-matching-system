const API_URL = 'http://localhost:8000';

// Получаем ID вакансии из URL
const urlParams = new URLSearchParams(window.location.search);
const vacancyId = urlParams.get('id');

if (!vacancyId) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('error').innerHTML = `
        <div class="error-message">
             ID вакансии не указан
        </div>
    `;
    document.getElementById('error').style.display = 'block';
} else {
    loadVacancy(vacancyId);
}

async function loadVacancy(id) {
    try {
        const response = await fetch(`${API_URL}/api/vacancies/${id}`);

        if (!response.ok) {
            throw new Error('Вакансия не найдена');
        }

        const vacancy = await response.json();
        displayVacancy(vacancy);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').innerHTML = `
            <div class="error-message">
                 Ошибка загрузки вакансии: ${error.message}
            </div>
        `;
        document.getElementById('error').style.display = 'block';
    }
}

function displayVacancy(vacancy) {
    // Скрываем загрузку
    document.getElementById('loading').style.display = 'none';
    document.getElementById('vacancyContent').style.display = 'block';

    // Заголовок
    document.getElementById('vacancyTitle').textContent = vacancy.title;

    // Мета-информация
    let metaInfo = [];
    if (vacancy.location) {
        metaInfo.push(`· ${vacancy.location}`);
    }
    if (vacancy.salary_min || vacancy.salary_max) {
        let salary = '';
        if (vacancy.salary_min && vacancy.salary_max) {
            salary = `💰 ${vacancy.salary_min.toLocaleString()} - ${vacancy.salary_max.toLocaleString()} ₽`;
        } else if (vacancy.salary_min) {
            salary = `💰 от ${vacancy.salary_min.toLocaleString()} ₽`;
        } else {
            salary = `💰 до ${vacancy.salary_max.toLocaleString()} ₽`;
        }
        metaInfo.push(salary);
    }
    if (vacancy.created_at) {
        const date = new Date(vacancy.created_at);
        metaInfo.push(`📅 Создано: ${date.toLocaleDateString('ru-RU')}`);
    }

    if (metaInfo.length > 0) {
        document.getElementById('vacancyLocation').textContent = metaInfo[0];
        if (metaInfo.length > 1) {
            document.getElementById('vacancySalary').textContent = ' • ' + metaInfo[1];
        }
        if (metaInfo.length > 2) {
            document.getElementById('vacancyDate').textContent = ' • ' + metaInfo[2];
        }
    }

    // Описание
    document.getElementById('vacancyDescription').textContent = vacancy.description;

    // Требования
    if (vacancy.requirements) {
        document.getElementById('vacancyRequirements').textContent = vacancy.requirements;
        document.getElementById('requirementsSection').style.display = 'block';
    }

    // Кнопка редактирования
    document.getElementById('editBtn').href = `edit-vacancy.html?id=${vacancy.id}`;
}
