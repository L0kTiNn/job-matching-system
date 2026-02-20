const API_URL = 'http://localhost:8000';

const urlParams = new URLSearchParams(window.location.search);
const vacancyId = urlParams.get('vacancy_id') || urlParams.get('id');
const resumeId = urlParams.get('resume_id');

if (!vacancyId) {
    showError('ID вакансии не указан');
} else {
    if (resumeId) {
        loadVacancyWithAnalysis();
    } else {
        loadVacancyDetails();
    }
}

// ============= ОБЫЧНЫЙ ПРОСМОТР =============
async function loadVacancyDetails() {
    try {
        const response = await fetch(`${API_URL}/api/vacancies/${vacancyId}`);

        if (!response.ok) {
            throw new Error('Вакансия не найдена');
        }

        const vacancy = await response.json();
        displayVacancy(vacancy);

    } catch (error) {
        console.error('Error:', error);
        showError('Не удалось загрузить вакансию');
    }
}

function displayVacancy(vacancy) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('vacancyContent').style.display = 'block';

    document.getElementById('vacancyTitle').textContent = vacancy.title;
    document.getElementById('vacancyLocation').textContent = ` ${vacancy.location || 'Не указано'}`;

    const salaryText = formatSalary(vacancy.salary_min, vacancy.salary_max);
    document.getElementById('vacancySalary').textContent = ` |  ${salaryText}`;

    if (vacancy.created_at) {
        const date = new Date(vacancy.created_at);
        document.getElementById('vacancyDate').textContent = ` |  ${date.toLocaleDateString('ru-RU')}`;
    }

    document.getElementById('vacancyDescription').textContent = vacancy.description || 'Описание не указано';

    if (vacancy.requirements) {
        document.getElementById('requirementsSection').style.display = 'block';
        document.getElementById('vacancyRequirements').textContent = vacancy.requirements;
    }

    document.getElementById('editBtn').href = `edit-vacancy.html?id=${vacancy.id}`;
}

// ============= ПРОСМОТР С АНАЛИЗОМ =============
async function loadVacancyWithAnalysis() {
    try {
        const response = await fetch(
            `${API_URL}/api/resumes/${resumeId}/vacancies/${vacancyId}/match-analysis`
        );

        if (!response.ok) {
            throw new Error('Не удалось загрузить анализ');
        }

        const data = await response.json();
        displayVacancyWithAnalysis(data);

    } catch (error) {
        console.error('Error:', error);
        showError('Не удалось загрузить анализ совпадений');
    }
}

function displayVacancyWithAnalysis(data) {
    document.getElementById('loading').style.display = 'none';

    const container = document.querySelector('.vacancy-detail');
    const matchPercent = Math.round(data.match_percentage);

    //  Определяем класс бейджа
    let badgeClass = 'low';
    let emoji = '';
    if (matchPercent >= 90) {
        badgeClass = 'excellent';
        emoji = '';
    } else if (matchPercent >= 70) {
        badgeClass = 'good';
        emoji = '';
    } else if (matchPercent >= 50) {
        badgeClass = 'medium';
        emoji = '';
    }

    container.innerHTML = `
        <!-- Заголовок с процентом -->
        <div class="vacancy-header" style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="flex: 1;">
                <h1 class="vacancy-title">${data.vacancy_title}</h1>
                <div class="vacancy-meta">
                    <span> ${data.vacancy_location}</span>
                    <span> |  ${data.vacancy_salary}</span>
                </div>
            </div>
            <div class="match-percentage ${badgeClass}">
                ${emoji} ${matchPercent}%
            </div>
        </div>

        <!-- Описание вакансии -->
        <div class="vacancy-section" style="margin-top: 30px;">
            <h3> Описание вакансии</h3>
            <p>${data.vacancy_description || 'Описание не указано'}</p>
        </div>

        <!-- Совпавшие навыки -->
        <div class="vacancy-section">
            <h3 style="border-left-color: #ff6b35; color: #ff6b35;">
                 Ваши навыки совпали (${data.matched_skills.length})
            </h3>
            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;">
                ${data.matched_skills.length > 0
                    ? data.matched_skills.map(skill => `
                        <span class="skill-badge skill-matched">
                            ✓ ${skill}
                        </span>
                    `).join('')
                    : '<p style="color: #999;">Совпадений не найдено</p>'
                }
            </div>
        </div>

        <!-- Критичные недостающие навыки -->
        ${data.critical_missing_skills && data.critical_missing_skills.length > 0 ? `
            <div class="vacancy-section">
                <h3 style="border-left-color: #2c2c2c; color: #2c2c2c;">
                     Критичные навыки, которых не хватает (${data.critical_missing_skills.length})
                </h3>
                <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;">
                    ${data.critical_missing_skills.map(skill => `
                        <span class="skill-badge skill-critical">
                             ${skill}
                        </span>
                    `).join('')}
                </div>
            </div>
        ` : ''}

        <!-- Недостающие навыки -->
        <div class="vacancy-section">
            <h3 style="border-left-color: #999; color: #666;">
                 Навыки, которых не хватает (${data.missing_skills.length})
            </h3>
            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;">
                ${data.missing_skills.length > 0
                    ? data.missing_skills.map(skill => `
                        <span class="skill-badge skill-missing">
                            ✗ ${skill}
                        </span>
                    `).join('')
                    : '<p style="color: #28a745; font-weight: 600;"> Все требуемые навыки присутствуют!</p>'
                }
            </div>
        </div>

        <!-- Дополнительные навыки -->
        ${data.extra_skills.length > 0 ? `
            <div class="vacancy-section">
                <h3 style="border-left-color: #66bb6a; color: #2e7d32;">
                     Ваши дополнительные навыки (+${data.extra_skills_bonus || 0}%)
                </h3>
                <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;">
                    ${data.extra_skills.map(skill => `
                        <span class="skill-badge skill-extra">
                            + ${skill}
                        </span>
                    `).join('')}
                </div>
            </div>
        ` : ''}

        <!-- Рекомендации -->
        <div class="recommendations-box">
            <h3> Персонализированные рекомендации</h3>
            <div class="content">${data.recommendations}</div>
        </div>


        <!-- Кнопки действий -->
        <div class="vacancy-actions">
            <button class="btn btn-edit" onclick="applyToVacancy(${data.vacancy_id})">
                ✉ Откликнуться на вакансию
            </button>
            <a href="edit-resume.html?id=${data.resume_id}" class="btn btn-edit" style="background: #6c757d;">
                 Улучшить резюме
            </a>
            <a href="javascript:history.back()" class="btn btn-back">
                ← Назад
            </a>
        </div>
    `;
}

// ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============

function formatSalary(min, max) {
    if (!min && !max) return 'Не указана';
    if (min && max) return `${min.toLocaleString()} - ${max.toLocaleString()} ₽`;
    if (min) return `от ${min.toLocaleString()} ₽`;
    return `до ${max.toLocaleString()} ₽`;
}

function showError(message) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('error').style.display = 'block';
    document.getElementById('error').innerHTML = `
        <div class="error-message">
             ${message}
        </div>
        <a href="vacancies.html" class="btn btn-back" style="margin-top: 20px; display: inline-block;">
            ← Вернуться к списку вакансий
        </a>
    `;
}

function applyToVacancy(vacancyId) {
    if (confirm(`Отправить отклик на вакансию #${vacancyId}?`)) {
        alert(' Отклик отправлен! (Функционал сохранения откликов в разработке)');
    }
}
