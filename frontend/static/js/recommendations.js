const API_URL = 'http://localhost:8000';

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

async function loadRecommendations() {
    try {
        const response = await fetch(`${API_URL}/api/resumes/${resumeId}/recommendations?limit=20`);

        if (!response.ok) {
            throw new Error('Ошибка загрузки рекомендаций');
        }

        const data = await response.json();
        displayResumeInfo(resumeId);
        await displayRecommendationsWithMatches(data.recommendations);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('recommendationsList').innerHTML = `
            <div class="error-message">
                 Не удалось загрузить рекомендации. Проверьте подключение к API.
            </div>
        `;
    }
}

function displayResumeInfo(id) {
    document.getElementById('resumeInfo').innerHTML = `
        <div class="resume-info-box">
            <h2> Резюме успешно создано!</h2>
            <p>
                ID резюме: <strong>${id}</strong><br>
                 Система проанализировала ваше резюме с помощью <strong>искусственного интеллекта</strong>
                и подобрала наиболее подходящие вакансии с учётом семантического сравнения навыков.
            </p>
        </div>
    `;
}

async function displayRecommendationsWithMatches(recommendations) {
    const container = document.getElementById('recommendationsList');

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = `
            <div class="empty-message">
                <div style="font-size: 48px; margin-bottom: 20px;"></div>
                К сожалению, подходящих вакансий пока не найдено.<br>
                Попробуйте создать резюме с другими навыками.
            </div>
        `;
        return;
    }

    // Сначала отрисовываем карточки
    container.innerHTML = recommendations.map(vacancy => `
        <div class="vacancy-card loading" id="vacancy-${vacancy.id}">
            <div class="match-badge loading">⏳ Анализ...</div>

            <h3 class="vacancy-title">${vacancy.title}</h3>

            ${vacancy.description ? `
                <p class="vacancy-description">
                    ${vacancy.description.substring(0, 150)}${vacancy.description.length > 150 ? '...' : ''}
                </p>
            ` : ''}

            <div class="vacancy-details">
                <div class="detail-item">
                    📍 <span>${vacancy.location || 'Не указано'}</span>
                </div>
            </div>

            <div class="vacancy-salary">
                ${formatSalary(vacancy.salary_min, vacancy.salary_max)}
            </div>

            <div class="vacancy-buttons">
                <button class="btn-details" onclick="viewVacancyDetails(${vacancy.id})">
                    👁 Детали
                </button>
                <button class="btn-apply" onclick="applyToVacancy(${vacancy.id})">
                    ✉ Откликнуться
                </button>
            </div>
        </div>
    `).join('');

    //  Загружаем проценты и собираем результаты
    const matchResults = [];

    for (const vacancy of recommendations) {
        const matchData = await loadMatchPercentage(vacancy.id);
        if (matchData) {
            matchResults.push({
                id: vacancy.id,
                percentage: matchData.match_percentage
            });
        }
    }

    //  Сортируем карточки по проценту
    if (matchResults.length > 0) {
        sortVacanciesByMatch(matchResults);
    }
}

//  Пересортировка карточек
function sortVacanciesByMatch(matchResults) {
    const container = document.getElementById('recommendationsList');

    // Сортируем ID по убыванию процента
    const sortedIds = matchResults
        .sort((a, b) => b.percentage - a.percentage)
        .map(item => item.id);

    // Перемещаем карточки в правильном порядке
    sortedIds.forEach(id => {
        const card = document.getElementById(`vacancy-${id}`);
        if (card) {
            container.appendChild(card);
        }
    });
}

async function loadMatchPercentage(vacancyId) {
    try {
        const response = await fetch(
            `${API_URL}/api/resumes/${resumeId}/vacancies/${vacancyId}/match-analysis`
        );

        if (response.ok) {
            const data = await response.json();
            const matchPercent = Math.round(data.match_percentage);

            const card = document.getElementById(`vacancy-${vacancyId}`);
            if (card) {
                card.classList.remove('loading');
                card.classList.add('loaded');

                const badge = card.querySelector('.match-badge');
                if (badge) {
                    badge.classList.remove('loading');

                    let badgeClass;
                    let emoji;

                    if (matchPercent >= 90) {
                        badgeClass = 'excellent';
                        emoji = '';
                    } else if (matchPercent >= 70) {
                        badgeClass = 'good';
                        emoji = '';
                    } else if (matchPercent >= 50) {
                        badgeClass = 'medium';
                        emoji = '';
                    } else {
                        badgeClass = 'low';
                        emoji = ' ';
                    }

                    badge.classList.add(badgeClass);
                    badge.innerHTML = `${emoji} ${matchPercent}%`;
                }

                const detailsDiv = card.querySelector('.vacancy-details');
                if (detailsDiv && data.matched_skills && data.matched_skills.length > 0) {
                    const skillsPreview = data.matched_skills.slice(0, 3).join(', ');
                    const moreSkills = data.matched_skills.length > 3 ? ` +${data.matched_skills.length - 3}` : '';

                    const matchInfo = document.createElement('div');
                    matchInfo.className = 'matched-skills-box';
                    matchInfo.innerHTML = `
                        <strong>✨ Совпадающие навыки:</strong><br>
                        <span class="matched-skills-list">${skillsPreview}${moreSkills}</span>
                    `;
                    detailsDiv.appendChild(matchInfo);
                }
            }

            //  Возвращаем данные!
            return data;
        }
    } catch (error) {
        console.error(`Ошибка загрузки для вакансии ${vacancyId}:`, error);

        const card = document.getElementById(`vacancy-${vacancyId}`);
        if (card) {
            card.classList.remove('loading');
            card.classList.add('loaded');

            const badge = card.querySelector('.match-badge');
            if (badge) {
                badge.classList.remove('loading');
                badge.classList.add('low');
                badge.textContent = '❓ N/A';
            }
        }
    }

    return null; // Если ошибка
}

function formatSalary(min, max) {
    if (!min && !max) return ' Зарплата не указана';
    if (min && max) return ` ${min.toLocaleString()} - ${max.toLocaleString()} ₽`;
    if (min) return ` от ${min.toLocaleString()} ₽`;
    return ` до ${max.toLocaleString()} ₽`;
}

function applyToVacancy(vacancyId) {
    if (confirm(` Отправить отклик на вакансию #${vacancyId}?`)) {
        alert(' Отклик отправлен! (Функционал сохранения откликов в разработке)');
    }
}

function viewVacancyDetails(vacancyId) {
    window.location.href = `view-vacancy.html?resume_id=${resumeId}&vacancy_id=${vacancyId}`;
}
