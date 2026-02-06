"""
Telegram Bot для HR-системы отбора кандидатов.

Возможности:
- Загрузка резюме (текст или файл)
- Автоматическая проверка совместимости с вакансиями
- Диалог с уточняющими вопросами
- Просмотр открытых вакансий
- Просмотр результатов отбора
- Статистика кандидата
"""
import logging
import os
import tempfile
import asyncio
import json
from typing import Dict, Optional, List
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import Candidate, Position, Screening, Clarification
from app.agent_tools import AgentTools
from app.true_agent import TrueAgent
from app.cv_parser import CVParser
from app.config import settings

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_FOR_CV_TEXT, WAITING_FOR_ANSWERS, VIEWING_POSITION = range(3)

# Кэш для хранения состояния пользователей
user_sessions: Dict[int, Dict] = {}

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный обработчик ошибок Telegram-бота."""
    logger.exception("Ошибка при обработке апдейта: %s", context.error)
    try:
        # Пытаемся сообщить пользователю, если это возможно
        if isinstance(update, Update):
            if update.message:
                await update.message.reply_text(
                    "❌ Произошла внутренняя ошибка. Я уже записал её в лог. Попробуйте ещё раз."
                )
            elif update.callback_query and update.callback_query.message:
                await update.callback_query.message.reply_text(
                    "❌ Произошла внутренняя ошибка. Я уже записал её в лог. Попробуйте ещё раз."
                )
    except Exception:
        # Не даём error handler'у падать
        logger.exception("Не удалось отправить сообщение об ошибке пользователю")


def get_user_session(user_id: int) -> Dict:
    """Получить или создать сессию пользователя."""
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'candidate_id': None,
            'current_screening': None,
            'pending_questions': [],
            'current_position_id': None
        }
    return user_sessions[user_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    welcome_text = f"""
👋 Добро пожаловать, {user.first_name}!

Я HR-бот для отбора кандидатов. Вот что я умею:

📄 **Загрузить резюме**
Отправьте мне ваше резюме текстом или файлом (PDF, DOCX, TXT), и я проверю вашу совместимость с открытыми вакансиями.

💼 **Просмотр вакансий**
Посмотрите все открытые вакансии и узнайте, подходите ли вы.

📊 **Моя статистика**
Узнайте результаты ваших отборов и совместимость с вакансиями.

❓ **Помощь**
Используйте /help для получения справки.

Начните с отправки резюме или используйте команды ниже!
"""
    
    keyboard = [
        [KeyboardButton("📄 Загрузить резюме"), KeyboardButton("💼 Вакансии")],
        [KeyboardButton("📊 Моя статистика"), KeyboardButton("❓ Помощь")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help."""
    help_text = """
📖 **Справка по командам:**

/start - Начать работу с ботом
/help - Показать эту справку
/cv - Загрузить резюме
/positions - Показать открытые вакансии
/stats - Моя статистика
/cancel - Отменить текущую операцию

**Как это работает:**
1. Отправьте резюме (текстом или файлом)
2. Система автоматически проверит совместимость с вакансиями
3. Если нужны уточнения - ответьте на вопросы
4. Получите результаты отбора

**Поддерживаемые форматы:**
- Текст (просто отправьте резюме текстом)
- PDF файлы
- DOCX файлы
- TXT файлы
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменить текущую операцию."""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    session['waiting_for_cv'] = False
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END


async def handle_cv_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /cv."""
    # Установить флаг ожидания CV
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    session['waiting_for_cv'] = True
    
    await update.message.reply_text(
        "📄 Отправьте ваше резюме:\n\n"
        "• Текстом (просто напишите резюме)\n"
        "• Или файлом (PDF, DOCX, TXT)\n\n"
        "Используйте /cancel для отмены."
    )
    return WAITING_FOR_CV_TEXT


async def process_cv_text(update: Update, context: ContextTypes.DEFAULT_TYPE, cv_text: str, db: Optional[Session] = None) -> None:
    """Обработать текст резюме."""
    user_id = update.effective_user.id
    close_db = False
    
    if db is None:
        db = SessionLocal()
        close_db = True
    
    try:
        await update.message.reply_text("⏳ Обрабатываю ваше резюме...")
        
        tools = AgentTools(db)
        
        # Сохранить текст во временный файл
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
        temp_file.write(cv_text)
        temp_file.close()
        
        # Создать кандидата
        candidate = await tools.create_candidate_from_file(temp_file.name, 'txt')
        os.unlink(temp_file.name)
        
        # Сохранить в сессию
        session = get_user_session(user_id)
        session['candidate_id'] = candidate.id
        
        # Обновить профиль с Telegram данными
        profile = candidate.structured_profile or {}
        profile['telegram'] = f"@{update.effective_user.username}" if update.effective_user.username else None
        profile['telegram_id'] = str(user_id)
        candidate.structured_profile = profile
        db.commit()
        
        # Проверить совместимость с вакансиями
        await check_compatibility(update, context, candidate.id, db)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке резюме: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при обработке резюме: {str(e)}\n\n"
            "Попробуйте еще раз или используйте /help для справки."
        )
    finally:
        if close_db:
            db.close()


async def process_cv_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    file_path: str,
    file_ext: str,
    db: Optional[Session] = None
) -> None:
    """Обработать файл (PDF/DOCX/TXT) и, если это резюме, создать кандидата и запустить проверку."""
    user_id = update.effective_user.id
    close_db = False

    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        tools = AgentTools(db)

        await update.message.reply_text("⏳ Проверяю содержимое файла...")

        parser = CVParser()
        extracted_text = await parser.parse_file(file_path, file_ext)

        is_cv = tools.llm.is_cv_content(extracted_text)
        if not is_cv:
            await update.message.reply_text(
                "❌ Похоже, это не резюме (CV).\n\n"
                "Если вы хотите загрузить резюме, отправьте файл с резюме или используйте /cv."
            )
            return

        await update.message.reply_text("⏳ Обрабатываю ваше резюме...")

        candidate = await tools.create_candidate_from_file(file_path, file_ext)

        session = get_user_session(user_id)
        session['candidate_id'] = candidate.id
        session['waiting_for_cv'] = False

        # Обновить профиль с Telegram данными
        profile = candidate.structured_profile or {}
        profile['telegram'] = f"@{update.effective_user.username}" if update.effective_user.username else None
        profile['telegram_id'] = str(user_id)
        candidate.structured_profile = profile
        db.commit()

        await check_compatibility(update, context, candidate.id, db)

    except Exception as e:
        logger.error(f"Ошибка при обработке файла: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при обработке файла: {str(e)}\n\n"
            "Попробуйте еще раз или используйте /help для справки."
        )
    finally:
        if close_db:
            db.close()


async def handle_cv_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка текстового резюме (для conversation handler)."""
    cv_text = update.message.text
    db = SessionLocal()
    try:
        await process_cv_text(update, context, cv_text, db)
        return ConversationHandler.END
    finally:
        db.close()


async def handle_cv_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка файла резюме."""
    user_id = update.effective_user.id
    document = update.message.document
    
    if not document:
        await update.message.reply_text("Пожалуйста, отправьте файл.")
        return WAITING_FOR_CV_TEXT
    
    # Если вызывается из conversation handler, мы уже в правильном состоянии
    # Но проверим флаг для ясности
    session = get_user_session(user_id)
    if not session.get('waiting_for_cv'):
        # Если файл отправлен, но флаг не установлен, возможно это вне conversation
        # Но так как мы удалили глобальный обработчик файлов, это не должно происходить
        # Установим флаг и продолжим (на случай если что-то пошло не так)
        session['waiting_for_cv'] = True
    
    # Проверить тип файла
    file_ext = document.file_name.split('.')[-1].lower() if document.file_name else ''
    if file_ext not in ['pdf', 'docx', 'txt']:
        await update.message.reply_text(
            "❌ Неподдерживаемый формат файла.\n\n"
            "Поддерживаются: PDF, DOCX, TXT\n"
            "Попробуйте отправить файл в одном из этих форматов."
        )
        return WAITING_FOR_CV_TEXT
    
    try:
        # Скачать файл
        file = await context.bot.get_file(document.file_id)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}')
        await file.download_to_drive(temp_file.name)
        temp_file.close()

        await process_cv_file(update, context, temp_file.name, file_ext)

        try:
            os.unlink(temp_file.name)
        except Exception:
            pass
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Ошибка при обработке файла: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при обработке файла: {str(e)}\n\n"
            "Попробуйте еще раз или используйте /help для справки."
        )
        return ConversationHandler.END


async def find_best_matching_positions(candidate, positions: List[Position], tools: AgentTools, top_n: int = 5) -> List[Position]:
    """
    Использовать LLM для определения наиболее подходящих позиций для кандидата.
    Не использует жестко заданные категории, а анализирует совместимость через LLM.
    """
    if not positions or not candidate or not candidate.structured_profile:
        return positions[:top_n] if positions else []
    
    profile = candidate.structured_profile
    
    # Собрать информацию о кандидате
    candidate_info = {
        "summary": profile.get('summary', ''),
        "experience": profile.get('experience', []),
        "skills": profile.get('skills', [])
    }
    
    # Собрать информацию о позициях
    positions_info = []
    for pos in positions:
        title = pos.structured_data.get('title', '') if pos.structured_data else ''
        requirements = pos.structured_data.get('requirements', []) if pos.structured_data else []
        positions_info.append({
            "id": pos.id,
            "title": title,
            "requirements": [req.get('text', '') for req in requirements[:10]]  # Первые 10 требований
        })
    
    # Использовать LLM для ранжирования позиций
    system_prompt = """Вы HR-специалист, который определяет, какие вакансии наиболее подходят кандидату на основе их опыта и навыков.

Проанализируйте профиль кандидата и список вакансий. Верните JSON массив с ID позиций, отсортированных по релевантности (от наиболее подходящих к наименее подходящим).

Верните ТОЛЬКО JSON массив строк с ID позиций в порядке релевантности:
["position_id_1", "position_id_2", ...]"""

    candidate_str = f"""
Кандидат:
Резюме: {candidate_info['summary']}
Опыт: {', '.join([exp.get('role', '') for exp in candidate_info['experience'][:3]])}
Навыки: {', '.join(candidate_info['skills'][:20])}
"""

    positions_str = "\n".join([
        f"ID: {p['id']}, Название: {p['title']}, Требования: {', '.join(p['requirements'][:5])}"
        for p in positions_info
    ])
    
    user_prompt = f"""{candidate_str}

Вакансии:
{positions_str}

Верните JSON массив ID позиций в порядке релевантности (от наиболее подходящих)."""

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = tools.llm._call_llm(messages, response_format={"type": "json_object"})
        result = json.loads(response)
        
        # Извлечь отсортированные ID
        sorted_ids = result.get("positions", []) if isinstance(result, dict) else result if isinstance(result, list) else []
        
        # Создать словарь позиций по ID
        positions_dict = {pos.id: pos for pos in positions}
        
        # Отсортировать позиции согласно LLM ранжированию
        sorted_positions = []
        for pos_id in sorted_ids:
            if pos_id in positions_dict:
                sorted_positions.append(positions_dict[pos_id])
        
        # Добавить позиции, которые LLM не вернул (на случай если что-то пропустил)
        for pos in positions:
            if pos.id not in sorted_ids:
                sorted_positions.append(pos)
        
        return sorted_positions[:top_n]
        
    except Exception as e:
        logger.error(f"Ошибка при ранжировании позиций через LLM: {e}")
        # Fallback: вернуть все позиции
        return positions[:top_n]


async def check_compatibility(update: Update, context: ContextTypes.DEFAULT_TYPE, candidate_id: str, db: Optional[Session] = None) -> None:
    """Проверить совместимость кандидата с открытыми вакансиями."""
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        tools = AgentTools(db)
        candidate = tools.get_candidate(candidate_id)
        
        if not candidate:
            await update.message.reply_text("❌ Кандидат не найден.")
            return
        
        # Найти открытые вакансии
        open_positions = db.query(Position).filter(Position.is_open == True).all()
        
        if not open_positions:
            await update.message.reply_text(
                "✅ Ваше резюме успешно загружено!\n\n"
                "Однако в данный момент нет открытых вакансий.\n"
                "Используйте /positions для просмотра вакансий позже."
            )
            return
        
        # Быстрый отбор top-K позиций через embeddings (кешируется в БД внутри JSON)
        await update.message.reply_text("⏳ Подбираю наиболее релевантные вакансии...")
        try:
            positions_to_check = tools.retrieve_top_positions_for_candidate(candidate_id, top_n=5)
        except Exception as e:
            logger.error(f"Ошибка при подборе релевантных вакансий: {e}")
            positions_to_check = open_positions[:5]
        
        await update.message.reply_text(
            f"✅ Резюме загружено! Проверяю совместимость с {len(positions_to_check)} вакансиями...\n\n"
            "⏳ Это может занять некоторое время..."
        )
        
        # Проверить совместимость с каждой вакансией
        matches = []
        for position in positions_to_check:
            try:
                # Использовать TrueAgent для проверки
                agent = TrueAgent(db, tools.llm)
                screening = agent.run_autonomous_screening(
                    candidate_id=candidate_id,
                    position_id=position.id,
                    max_iterations=3
                )
                
                matches.append({
                    'position': position,
                    'screening': screening,
                    'score': screening.score,
                    'decision': screening.decision
                })
            except Exception as e:
                logger.error(f"Ошибка при проверке вакансии {position.id}: {e}")
                continue
        
        # Отсортировать по оценке
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        if not matches:
            await update.message.reply_text(
                "✅ Проверка завершена, но результаты пока не готовы.\n\n"
                "Используйте /stats для просмотра результатов позже."
            )
            return
        
        # Показать результаты
        result_text = "📊 **Результаты проверки совместимости:**\n\n"
        
        for i, match in enumerate(matches[:3], 1):  # Показать топ-3
            position = match['position']
            screening = match['screening']
            title = position.structured_data.get('title', 'Без названия') if position.structured_data else 'Без названия'
            
            decision_emoji = {
                'pass': '✅',
                'hold': '⏳',
                'reject': '❌'
            }.get(screening.decision, '❓')
            
            decision_text = {
                'pass': 'ПОДХОДИТЕ',
                'hold': 'НА РАССМОТРЕНИИ',
                'reject': 'Мы свяжемся с вами позже'
            }.get(screening.decision, 'НЕИЗВЕСТНО')
            
            result_text += f"{i}. {title}\n"
            result_text += f"   {decision_emoji} {decision_text} ({screening.score*100:.1f}%)\n\n"
        
        # Проверить, нужны ли уточняющие вопросы
        best_match = matches[0]
        screening = best_match['screening']
        
        if screening.clarification_questions and len(screening.clarification_questions) > 0:
            session = get_user_session(update.effective_user.id)
            session['current_screening'] = screening.id
            session['pending_questions'] = screening.clarification_questions
            session['current_position_id'] = best_match['position'].id
            
            await ask_clarification_questions(update, context, screening.clarification_questions)
        else:
            await update.message.reply_text(
                result_text + "\n\n"
                "💡 Используйте /positions для просмотра всех вакансий.\n"
                "📊 Используйте /stats для подробной статистики.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Ошибка при проверке совместимости: {e}")
        await update.message.reply_text("❌ Ошибка при проверке совместимости.")


async def ask_clarification_questions(update: Update, context: ContextTypes.DEFAULT_TYPE, questions: List[str]) -> None:
    """Задать уточняющие вопросы."""
    if not questions:
        return
    
    question_text = "❓ **Уточняющие вопросы:**\n\n"
    question_text += f"1. {questions[0]}\n\n"
    question_text += "Пожалуйста, ответьте на вопрос текстом."
    
    await update.message.reply_text(question_text, parse_mode='Markdown')
    
    # Сохранить состояние
    session = get_user_session(update.effective_user.id)
    session['current_question_index'] = 0


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработать ответ на уточняющий вопрос."""
    user_id = update.effective_user.id
    answer = update.message.text
    session = get_user_session(user_id)
    
    if not session.get('pending_questions'):
        return
    
    current_index = session.get('current_question_index', 0)
    questions = session['pending_questions']
    candidate_id = session.get('candidate_id')
    screening_id = session.get('current_screening')
    position_id = session.get('current_position_id')
    
    if not candidate_id or not screening_id:
        await update.message.reply_text("Ошибка: сессия не найдена. Начните заново с /start")
        return
    
    db = SessionLocal()
    try:
        
        # Сохранить ответ
        question = questions[current_index]
        # Найти или создать clarification
        clarification = db.query(Clarification).filter(
            Clarification.candidate_id == candidate_id,
            Clarification.question == question
        ).first()
        
        if not clarification:
            clarification = Clarification(
                candidate_id=candidate_id,
                question=question,
                answer=answer,
                answered_at=datetime.now()
            )
            db.add(clarification)
        else:
            clarification.answer = answer
            clarification.answered_at = datetime.now()
        
        db.commit()
        
        # Проверить, есть ли еще вопросы
        if current_index + 1 < len(questions):
            session['current_question_index'] = current_index + 1
            next_question = questions[current_index + 1]
            await update.message.reply_text(
                f"✅ Спасибо за ответ!\n\n"
                f"❓ **Следующий вопрос:**\n\n"
                f"{next_question}\n\n"
                f"Пожалуйста, ответьте текстом."
            )
        else:
            # Все вопросы отвечены, переоценить
            await update.message.reply_text(
                "✅ Все вопросы отвечены! Переоцениваю вашу кандидатуру...\n\n"
                "⏳ Это может занять некоторое время..."
            )
            
            # Использовать TrueAgent для обработки ответов
            tools = AgentTools(db)
            agent = TrueAgent(db, tools.llm)
            
            # Получить все ответы
            answers = {}
            for q in questions:
                clar = db.query(Clarification).filter(
                    Clarification.candidate_id == candidate_id,
                    Clarification.question == q
                ).first()
                if clar and clar.answer:
                    answers[q] = clar.answer
            
            # Обработать ответы через TrueAgent и обновить профиль
            if answers:
                # 1) Обновить structured_profile кандидата на основе ответов
                agent._tool_process_answers(candidate_id, answers, screening_id)

                # 2) Переоценить кандидата для этой же вакансии (создаст новую версию отбора)
                reeval_result = agent._tool_reevaluate(
                    candidate_id=candidate_id,
                    position_id=position_id,
                    previous_screening_id=screening_id
                )

                if not reeval_result.get("success"):
                    logger.error(f"Ошибка при переоценке: {reeval_result}")
                    await update.message.reply_text(
                        "❌ Не удалось выполнить повторную оценку после ответов.\n"
                        "Попробуйте позже или свяжитесь с HR."
                    )
                else:
                    # Получить обновленный Screening из БД, чтобы отобразить точные данные
                    new_screening_id = reeval_result.get("screening_id")
                    db_screening = db.query(Screening).filter(Screening.id == new_screening_id).first()
                    screening_obj = db_screening or new_screening_id

                    # Обновить текущий screening в сессии
                    session['current_screening'] = new_screening_id

                    decision = reeval_result.get("decision") or (db_screening.decision if db_screening else None)
                    score = reeval_result.get("score") if isinstance(reeval_result.get("score"), (int, float)) else (db_screening.score if db_screening else 0.0)

                    decision_emoji = {
                        'pass': '✅',
                        'hold': '⏳',
                        'reject': '❌'
                    }.get(decision, '❓')
                    
                    decision_text = {
                        'pass': 'ПОДХОДИТЕ',
                        'hold': 'НА РАССМОТРЕНИИ',
                        'reject': 'Мы свяжемся с вами позже'
                    }.get(decision, 'НЕИЗВЕСТНО')
                    
                    await update.message.reply_text(
                        f"📊 **Обновленный результат (версия {reeval_result.get('version', '?')}):**\n\n"
                        f"{decision_emoji} {decision_text}\n"
                        f"Оценка: {score*100:.1f}%\n\n"
                        f"Используйте /stats для просмотра всех версий отбора и подробностей."
                    )
            
            # Очистить сессию по вопросам
            session['pending_questions'] = []
            session['current_question_index'] = 0
            
    except Exception as e:
        logger.error(f"Ошибка при обработке ответа: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при обработке ответа: {str(e)}"
        )
    finally:
        db.close()


async def show_positions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать открытые вакансии."""
    db = SessionLocal()
    try:
        positions = db.query(Position).filter(Position.is_open == True).order_by(Position.created_at.desc()).limit(10).all()
        
        if not positions:
            await update.message.reply_text("В данный момент нет открытых вакансий.")
            return
        
        text = f"💼 **Открытые вакансии ({len(positions)}):**\n\n"
        
        keyboard = []
        for position in positions:
            title = position.structured_data.get('title', 'Без названия') if position.structured_data else 'Без названия'
            text += f"• {title}\n"
            keyboard.append([InlineKeyboardButton(
                title,
                callback_data=f"position_{position.id}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка при получении вакансий: {e}")
        await update.message.reply_text("❌ Ошибка при получении вакансий.")
    finally:
        db.close()


async def show_position_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, position_id: str) -> None:
    """Показать детали вакансии."""
    db = SessionLocal()
    try:
        tools = AgentTools(db)
        position = tools.get_position(position_id)
        
        if not position:
            await update.callback_query.answer("Вакансия не найдена")
            return
        
        title = position.structured_data.get('title', 'Без названия') if position.structured_data else 'Без названия'
        requirements = position.structured_data.get('requirements', []) if position.structured_data else []
        
        text = f"💼 **{title}**\n\n"
        
        if requirements:
            text += "**Требования:**\n"
            for req in requirements[:5]:  # Показать первые 5
                category_emoji = {
                    'must': '🔴',
                    'nice': '🟡',
                    'bonus': '🟢'
                }.get(req.get('category', 'nice'), '⚪')
                text += f"{category_emoji} {req.get('text', '')}\n"
        
        # Проверить, есть ли кандидат в сессии
        user_id = update.effective_user.id
        session = get_user_session(user_id)
        candidate_id = session.get('candidate_id')
        
        if candidate_id:
            keyboard = [[InlineKeyboardButton(
                "✅ Проверить совместимость",
                callback_data=f"check_{position_id}"
            )]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reply_markup = None
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка при получении вакансии: {e}")
        await update.callback_query.answer("Ошибка при получении вакансии")
    finally:
        db.close()


async def check_position_compatibility(update: Update, context: ContextTypes.DEFAULT_TYPE, position_id: str) -> None:
    """Проверить совместимость с конкретной вакансией."""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    candidate_id = session.get('candidate_id')
    
    if not candidate_id:
        await update.callback_query.answer("Сначала загрузите резюме с помощью /cv")
        return
    
    await update.callback_query.answer("Проверяю совместимость...")
    await update.callback_query.edit_message_text("⏳ Проверяю вашу совместимость с вакансией...")
    
    try:
        db = next(get_db())
        tools = AgentTools(db)
        agent = TrueAgent(db, tools.llm)
        
        screening = agent.run_autonomous_screening(
            candidate_id=candidate_id,
            position_id=position_id,
            max_iterations=3
        )
        
        decision_emoji = {
            'pass': '✅',
            'hold': '⏳',
            'reject': '❌'
        }.get(screening.decision, '❓')
        
        decision_text = {
            'pass': 'ПОДХОДИТЕ',
            'hold': 'НА РАССМОТРЕНИИ',
            'reject': 'Мы свяжемся с вами позже'
        }.get(screening.decision, 'НЕИЗВЕСТНО')
        
        text = f"📊 **Результат проверки:**\n\n"
        text += f"{decision_emoji} {decision_text}\n"
        text += f"Оценка: {screening.score*100:.1f}%\n\n"
        
        if screening.clarification_questions:
            text += "❓ Есть уточняющие вопросы. Используйте /stats для просмотра."
        
        await update.callback_query.edit_message_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка при проверке совместимости: {e}")
        await update.callback_query.edit_message_text("❌ Ошибка при проверке совместимости.")
    finally:
        db.close()


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать статистику кандидата."""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    candidate_id = session.get('candidate_id')
    
    if not candidate_id:
        await update.message.reply_text(
            "Сначала загрузите резюме с помощью /cv или отправьте резюме текстом/файлом."
        )
        return
    
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        
        if not candidate:
            await update.message.reply_text("Кандидат не найден.")
            return
        
        # Получить все отборы
        screenings = db.query(Screening).filter(
            Screening.candidate_id == candidate_id
        ).order_by(Screening.created_at.desc()).limit(10).all()
        
        profile = candidate.structured_profile or {}
        name = profile.get('name', 'Не указано')
        
        text = f"📊 **Статистика кандидата:**\n\n"
        text += f"👤 Имя: {name}\n"
        text += f"📧 Email: {profile.get('email', 'Не указан')}\n"
        text += f"📱 Телефон: {profile.get('phone', 'Не указан')}\n\n"
        text += f"📈 Всего отборов: {len(screenings)}\n\n"
        
        if screenings:
            text += "**Последние результаты:**\n"
            for screening in screenings[:5]:
                position = db.query(Position).filter(Position.id == screening.position_id).first()
                title = position.structured_data.get('title', 'Без названия') if position.structured_data else 'Без названия'
                
                decision_emoji = {
                    'pass': '✅',
                    'hold': '⏳',
                    'reject': '❌'
                }.get(screening.decision, '❓')
                
                text += f"{decision_emoji} {title}: {screening.score*100:.1f}%\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await update.message.reply_text("❌ Ошибка при получении статистики.")
    finally:
        db.close()


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки."""
    query = update.callback_query
    data = query.data
    
    if data.startswith('position_'):
        position_id = data.replace('position_', '')
        await show_position_detail(update, context, position_id)
    elif data.startswith('check_'):
        position_id = data.replace('check_', '')
        await check_position_compatibility(update, context, position_id)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    text = update.message.text
    
    # Проверить, является ли это ответом на вопрос
    session = get_user_session(update.effective_user.id)
    if session.get('pending_questions'):
        await handle_answer(update, context)
        return
    
    # Обработка команд из клавиатуры
    if text == "📄 Загрузить резюме":
        await handle_cv_command(update, context)
    elif text == "💼 Вакансии":
        await show_positions(update, context)
    elif text == "📊 Моя статистика":
        await show_stats(update, context)
    elif text == "❓ Помощь":
        await help_command(update, context)
    else:
        # Использовать LLM для проверки, является ли текст резюме
        await update.message.reply_text("⏳ Проверяю, является ли это резюме...")
        
        db = SessionLocal()
        try:
            tools = AgentTools(db)
            is_cv = tools.llm.is_cv_content(text)
            
            if is_cv:
                # Это резюме, обработать его
                await process_cv_text(update, context, text, db)
            else:
                # Это не резюме, показать помощь
                await update.message.reply_text(
                    "Я не понимаю эту команду. Используйте кнопки ниже или команды:\n\n"
                    "/cv - Загрузить резюме\n"
                    "/positions - Просмотр вакансий\n"
                    "/stats - Моя статистика\n"
                    "/help - Справка"
                )
        except Exception as e:
            logger.error(f"Ошибка при проверке текста: {e}")
            await update.message.reply_text(
                "❌ Ошибка при обработке сообщения. Попробуйте использовать команды:\n\n"
                "/cv - Загрузить резюме\n"
                "/help - Справка"
            )
        finally:
            db.close()


def create_bot_application() -> Application:
    """Создать и настроить приложение бота."""
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN не установлен. Бот не будет запущен.")
        return None
    
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cv", handle_cv_command))
    application.add_handler(CommandHandler("positions", show_positions))
    application.add_handler(CommandHandler("stats", show_stats))
    
    # Conversation для загрузки CV (через команду /cv)
    cv_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("cv", handle_cv_command)
        ],
        states={
            WAITING_FOR_CV_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cv_text),
                MessageHandler(filters.Document.ALL, handle_cv_file)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(cv_conversation)
    
    # Обработчик файлов (для файлов, отправленных вне conversation)
    async def handle_file_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик файлов, отправленных вне conversation."""
        document = update.message.document
        if not document:
            return
        
        file_ext = document.file_name.split('.')[-1].lower() if document.file_name else ''
        if file_ext not in ['pdf', 'docx', 'txt']:
            await update.message.reply_text(
                "❌ Неподдерживаемый формат файла.\n\n"
                "Поддерживаются: PDF, DOCX, TXT"
            )
            return
        
        try:
            # Скачать файл
            file = await context.bot.get_file(document.file_id)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}')
            await file.download_to_drive(temp_file.name)
            temp_file.close()
            
            # Обработать файл
            await process_cv_file(update, context, temp_file.name, file_ext)
            
            # Удалить временный файл
            try:
                os.unlink(temp_file.name)
            except:
                pass
        except Exception as e:
            logger.error(f"Ошибка при обработке файла: {e}")
            await update.message.reply_text(
                f"❌ Ошибка при обработке файла: {str(e)}"
            )
    
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file_message))
    
    # Обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Обработчик текстовых сообщений (после всех остальных)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Глобальный обработчик ошибок, чтобы исключения не терялись и пользователь получал ответ
    application.add_error_handler(error_handler)
    
    return application


def start_bot() -> None:
    """Запустить бота."""
    application = create_bot_application()
    if not application:
        logger.warning("Telegram бот не запущен из-за отсутствия токена.")
        return
    
    logger.info("Запуск Telegram бота...")
    
    # Используем asyncio подход для более надежного запуска
    async def run_bot():
        logger.info("Внутри run_bot(), инициализирую application...")
        await application.initialize()
        logger.info("Application инициализирован, запускаю...")
        await application.start()
        logger.info("Application запущен")
        # start_polling запускает polling, но не блокирует
        logger.info("Вызываю start_polling...")
        try:
            await application.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"]
            )
            logger.info("start_polling завершился (это нормально, он не блокирует)")
        except Exception as e:
            logger.error(f"Ошибка в start_polling: {e}", exc_info=True)
            raise
        
        logger.info("Telegram бот запущен и готов к работе!")
        logger.info("Бот работает, ожидаю сообщения...")
        
        # Используем простой бесконечный цикл для поддержания работы
        # idle() может завершаться в некоторых версиях библиотеки
        try:
            logger.info("Вхожу в бесконечный цикл для поддержания работы...")
            while True:
                await asyncio.sleep(3600)  # Спать час, затем проверить снова
                logger.info("Бот все еще работает...")
        except asyncio.CancelledError:
            logger.info("Получен сигнал отмены...")
        except KeyboardInterrupt:
            logger.info("Получен KeyboardInterrupt...")
        finally:
            logger.info("Остановка бота...")
            await application.stop()
            await application.shutdown()
    
    try:
        logger.info("Вызываю asyncio.run(run_bot())...")
        asyncio.run(run_bot())
        logger.warning("asyncio.run(run_bot()) завершился (не должно происходить!)")
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    asyncio.run(start_bot())
