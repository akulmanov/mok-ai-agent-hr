"""
Простой тест для проверки конфигурации Telegram бота.
"""
import os
from app.config import settings

print("=" * 50)
print("Проверка конфигурации Telegram бота")
print("=" * 50)

# Проверка токена
if settings.telegram_bot_token:
    token_preview = settings.telegram_bot_token[:10] + "..." + settings.telegram_bot_token[-5:] if len(settings.telegram_bot_token) > 15 else "***"
    print(f"✅ TELEGRAM_BOT_TOKEN: {token_preview}")
else:
    print("❌ TELEGRAM_BOT_TOKEN: НЕ УСТАНОВЛЕН")
    print("\nДобавьте в .env файл:")
    print("TELEGRAM_BOT_TOKEN=your_token_here")

# Проверка других настроек
print(f"\n📁 Database URL: {settings.database_url}")
print(f"🤖 OpenAI Model: {settings.openai_model}")
print(f"📝 Log Level: {settings.log_level}")

# Проверка .env файла
if os.path.exists('.env'):
    print("\n✅ Файл .env найден")
    with open('.env', 'r', encoding='utf-8') as f:
        has_token = 'TELEGRAM_BOT_TOKEN' in f.read()
        if has_token:
            print("✅ TELEGRAM_BOT_TOKEN найден в .env")
        else:
            print("❌ TELEGRAM_BOT_TOKEN НЕ найден в .env")
else:
    print("\n⚠️  Файл .env не найден")

print("\n" + "=" * 50)
