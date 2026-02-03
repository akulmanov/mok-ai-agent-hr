"""
Скрипт для запуска Telegram бота.
"""
import asyncio
import logging
from app.telegram_bot import start_bot
from app.config import settings

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, settings.log_level)
    )
    
    if not settings.telegram_bot_token:
        print("⚠️  ВНИМАНИЕ: TELEGRAM_BOT_TOKEN не установлен в .env файле!")
        print("Создайте бота через @BotFather и добавьте токен в .env:")
        print("TELEGRAM_BOT_TOKEN=your_token_here")
        exit(1)
    
    try:
        logger.info("Запуск Telegram бота...")
        start_bot()
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        raise
