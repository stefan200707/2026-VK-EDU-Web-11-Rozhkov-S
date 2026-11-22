// Лайки/дизлайки и отметка правильного ответа через AJAX (fetch + CSRF-токен из cookie)

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const ERROR_TEXTS = {
    400: 'Неверные параметры запроса',
    403: 'Запрос отклонён: нет CSRF-токена. Обновите страницу и попробуйте ещё раз',
    404: 'Объект не найден',
    405: 'Неверный метод запроса',
};

// POST-запрос; возвращает JSON при успехе или null, если была ошибка (о ней уже сообщили пользователю)
async function postData(url, data) {
    const body = new FormData();
    for (const key in data) {
        body.append(key, data[key]);
    }

    let response;
    try {
        response = await fetch(url, {
            method: 'POST',
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            mode: 'same-origin',  // токен не уходит на чужие домены
            body: body,
        });
    } catch (e) {
        alert('Нет связи с сервером');
        return null;
    }

    let json = {};
    try {
        json = await response.json();
    } catch (e) {
        // ошибки CSRF и 405 Django отдаёт не JSON, а HTML
    }

    if (response.ok) {
        return json;
    }
    if (response.status === 401) {
        const next = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = (json.login_url || '/login/') + '?next=' + next;
        return null;
    }
    alert(json.error || ERROR_TEXTS[response.status] || `Ошибка сервера (${response.status})`);
    return null;
}

for (const button of document.querySelectorAll('.likes .like-btn[data-type]')) {
    button.addEventListener('click', async () => {
        const widget = button.closest('.likes');
        const data = await postData(widget.dataset.url, {id: widget.dataset.id, type: button.dataset.type});
        if (!data) {
            return;
        }
        widget.querySelector('.likes-count').innerText = data.rating;
        // поставленная оценка подсвечена и недоступна, другую можно выбрать
        for (const other of widget.querySelectorAll('.like-btn')) {
            const active = other === button;
            other.classList.toggle('active', active);
            other.disabled = active;
            other.setAttribute('aria-pressed', active);
        }
    });
}

for (const checkbox of document.querySelectorAll('.correct-checkbox')) {
    checkbox.addEventListener('change', async () => {
        const wanted = checkbox.checked;
        checkbox.checked = !wanted;  // до ответа сервера оставляем как было
        const data = await postData(checkbox.dataset.url, {
            question_id: checkbox.dataset.questionId,
            answer_id: checkbox.dataset.answerId,
        });
        if (!data) {
            return;
        }
        // правильный ответ у вопроса один: с остальных отметку снимаем
        for (const other of document.querySelectorAll('.correct-checkbox')) {
            other.checked = false;
        }
        checkbox.checked = data.is_correct;
    });
}
