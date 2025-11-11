import os
import resend

# Задайте API-ключ
resend.api_key = ""

# Параметры письма
params: resend.Emails.SendParams = {
    "from": "onboarding@resend.dev",       # либо свой проверенный домен
    "to": ["harmonifood.main@gmail.com"],
    "subject": "Привет",
    "html": "<p>Привет! Это тестовое письмо с onboarding dev.</p>"
}

# Отправка письма
try:
    email = resend.Emails.send(params)
    print("Отправлено успешно:", email)
except Exception as e:
    print("Ошибка при отправке:", e)