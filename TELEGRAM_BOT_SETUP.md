# Настройка Telegram бота

## ✅ Бот запущен в Docker!

Бот должен работать. Проверьте следующее:

## 1. Проверка токена

Убедитесь, что в файле `.env` есть строка:
```env
TELEGRAM_BOT_TOKEN=your_actual_token_here
```

## 2. Проверка работы бота

1. Откройте Telegram
2. Найдите вашего бота (имя, которое вы дали при создании через @BotFather)
3. Отправьте команду `/start`
4. Бот должен ответить приветственным сообщением

## 3. Управление ботом в Docker

### Просмотр логов:
```bash
docker-compose logs telegram-bot
```

### Просмотр логов в реальном времени:
```bash
docker-compose logs -f telegram-bot
```

### Перезапуск бота:
```bash
docker-compose restart telegram-bot
```

### Остановка бота:
```bash
docker-compose stop telegram-bot
```

### Запуск бота:
```bash
docker-compose start telegram-bot
```

## 4. Если бот не отвечает

1. **Проверьте токен:**
   ```bash
   docker-compose exec telegram-bot python -c "from app.config import settings; print('Token:', 'SET' if settings.telegram_bot_token else 'NOT SET')"
   ```

2. **Проверьте логи на ошибки:**
   ```bash
   docker-compose logs telegram-bot | findstr ERROR
   ```

3. **Проверьте, что контейнер запущен:**
   ```bash
   docker-compose ps telegram-bot
   ```

4. **Перезапустите бота:**
   ```bash
   docker-compose restart telegram-bot
   ```

## 5. Локальный запуск (без Docker)

Если хотите запустить локально, установите все зависимости:

```bash
pip install -r requirements.txt
```

Затем запустите:
```bash
python run_telegram_bot.py
```

## 6. Команды бота

- `/start` - Начать работу
- `/help` - Справка
- `/cv` - Загрузить резюме
- `/positions` - Показать вакансии
- `/stats` - Моя статистика
- `/cancel` - Отменить операцию

## 7. Полный запуск всех сервисов

```bash
docker-compose up -d
```

Это запустит:
- API (порт 8000)
- Frontend (порт 3000)
- Mailpit (порт 8025)
- Telegram Bot
