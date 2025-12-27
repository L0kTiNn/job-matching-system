const API_URL = 'http://localhost:8000';

document.getElementById('resumeForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Создание резюме...';

    const formData = {
        user_id: 1, // Временно
        title: document.getElementById('title').value,
        summary: document.getElementById('summary').value,
        skills: document.getElementById('skills').value,
        experience: document.getElementById('experience').value,
        education: document.getElementById('education').value,
        desired_position: document.getElementById('title').value,
        desired_salary: parseInt(document.getElementById('desired_salary').value) || null,
        location: document.getElementById('location').value
    };

    try {
        const response = await fetch(`${API_URL}/api/resumes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Ошибка создания резюме');
        }

        const result = await response.json();

        // Show success message
        document.getElementById('message').innerHTML = `
            <div class="success-message">
                 Резюме успешно создано! ID: ${result.id}<br>
                Перенаправляем на страницу с рекомендациями...
            </div>
        `;

        // Redirect to recommendations
        setTimeout(() => {
            window.location.href = `recommendations.html?resume_id=${result.id}`;
        }, 2000);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('message').innerHTML = `
            <div class="error-message">
                 Ошибка при создании резюме. Проверьте подключение к API.
            </div>
        `;
        submitBtn.disabled = false;
        submitBtn.textContent = 'Создать резюме';
    }
});
