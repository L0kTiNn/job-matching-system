const API_URL = 'http://localhost:8000';

// Получаем ID резюме из URL
const urlParams = new URLSearchParams(window.location.search);
const resumeId = urlParams.get('id');

if (!resumeId) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('message').innerHTML = `
        <div class="error-message">
            ❌ ID резюме не указан
        </div>
    `;
} else {
    loadResume(resumeId);
}

// Загрузка данных резюме
async function loadResume(id) {
    try {
        const response = await fetch(`${API_URL}/api/resumes/${id}`);

        if (!response.ok) {
            throw new Error('Резюме не найдено');
        }

        const resume = await response.json();
        fillForm(resume);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('message').innerHTML = `
            <div class="error-message">
                 Ошибка загрузки резюме: ${error.message}
            </div>
        `;
    }
}

// Заполнение формы данными
function fillForm(resume) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('editResumeForm').style.display = 'block';

    document.getElementById('title').value = resume.title || '';
    document.getElementById('summary').value = resume.summary || '';
    document.getElementById('skills').value = resume.skills || '';
    document.getElementById('experience').value = resume.experience || '';
    document.getElementById('education').value = resume.education || '';
    document.getElementById('desired_salary').value = resume.desired_salary || '';
    document.getElementById('location').value = resume.location || '';
}

// Обработка отправки формы
document.getElementById('editResumeForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = ' Сохранение...';

    const formData = {
        title: document.getElementById('title').value,
        summary: document.getElementById('summary').value || null,
        skills: document.getElementById('skills').value || null,
        experience: document.getElementById('experience').value || null,
        education: document.getElementById('education').value || null,
        desired_position: document.getElementById('title').value,
        desired_salary: parseInt(document.getElementById('desired_salary').value) || null,
        location: document.getElementById('location').value || null
    };

    try {
        const response = await fetch(`${API_URL}/api/resumes/${resumeId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Ошибка обновления резюме');
        }

        const result = await response.json();

        // Успешное сообщение
        document.getElementById('message').innerHTML = `
            <div class="success-message">
                 Резюме успешно обновлено!<br>
                Перенаправляем на страницу просмотра...
            </div>
        `;

        // Редирект на просмотр
        setTimeout(() => {
            window.location.href = `view-resume.html?id=${resumeId}`;
        }, 1500);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('message').innerHTML = `
            <div class="error-message">
                 Ошибка при обновлении резюме. Проверьте подключение к API.
            </div>
        `;
        submitBtn.disabled = false;
        submitBtn.textContent = ' Сохранить изменения';
    }
});
