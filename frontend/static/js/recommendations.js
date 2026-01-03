const API_URL = 'http://localhost:8000';

// Get resume ID from URL
const urlParams = new URLSearchParams(window.location.search);
const resumeId = urlParams.get('resume_id');

if (!resumeId) {
    document.getElementById('resumeInfo').innerHTML = `
        <div class="error-message">
             ID резюме не указан. <a href="create-resume.html">Создать резюме</a>
        </div>
    `;
} else {
    loadRecommendations();
}

// Load recommendations
async function loadRecommendations() {
    try {
        // Get recommendations
        const response = await fetch(`${API_URL}/api/resumes/${resumeId}/recommendations?limit=20`);

        if (!response.ok) {
            throw new Error('Ошибка загрузки рекомендаций');
        }

        const data = await response.json();

        // Display resume info
        displayResumeInfo(resumeId);

        // Display recommendations
        displayRecommendations(data.recommendations);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('recommendationsList').innerHTML = `
            <div class="error-message">
                 Не удалось загрузить рекомендации. Проверьте подключение к API.
            </div>
        `;
    }
}

// Display resume info
function displayResumeInfo(id) {
    document.getElementById('resumeInfo').innerHTML = `
        <h2 style="color: #2d2d2d; margin-bottom: 15px;"> Резюме успешно создано!</h2>
        <p style="color: #666; font-size: 16px;">
            ID резюме: <strong>${id}</strong><br>
            Система проанализировала ваше резюме с помощью искусственного интеллекта и подобрала наиболее подходящие вакансии.
        </p>
    `;
}

// Display recommendations
function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendationsList');

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = `
            <div class="loading">
                К сожалению, подходящих вакансий пока не найдено.<br>
                Попробуйте создать резюме с другими навыками.
            </div>
        `;
        return;
    }

    container.innerHTML = recommendations.map(vacancy => `
        <div class="vacancy-card" style="position: relative;">
            <!-- Процент совпадения справа сверху -->
            <div style="position: absolute; top: 15px; right: 15px; background: #667eea; color: white; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                Совпадение: ${Math.round(vacancy.similarity)}%
            </div>

            <h3 class="vacancy-title" style="margin-top: 10px;">${vacancy.title}</h3>

            ${vacancy.description ? `
                <p class="vacancy-company">${vacancy.description}</p>
            ` : ''}

            <div class="vacancy-details">
                <div class="detail-item">
                    📍 ${vacancy.location || 'Не указано'}
                </div>
            </div>

            <div class="vacancy-salary">
                ${formatSalary(vacancy.salary_min, vacancy.salary_max)}
            </div>

            <button class="btn-primary" style="margin-top: 20px; width: 100%;" onclick="applyToVacancy(${vacancy.id})">
                Откликнуться
            </button>
        </div>
    `).join('');
}

// Format salary
function formatSalary(min, max) {
    if (!min && !max) return 'Зарплата не указана';
    if (min && max) return `${min.toLocaleString()} - ${max.toLocaleString()} ₽`;
    if (min) return `от ${min.toLocaleString()} ₽`;
    return `до ${max.toLocaleString()} ₽`;
}

// Apply to vacancy
function applyToVacancy(vacancyId) {
    if (confirm(`Отправить отклик на вакансию #${vacancyId}?`)) {
        alert('Отклик отправлен! (Функционал сохранения откликов в разработке)');
    }
}
