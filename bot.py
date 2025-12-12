import os
import logging
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

openai_client = None

SYSTEM_PROMPT = """Ты эксперт по промпт-инжинирингу. Твоя задача — создавать профессиональные промпты с нуля на основе описания задачи пользователя.

Когда пользователь описывает свою задачу, ты должен:
1. Проанализировать описание задачи и понять цель пользователя
2. Создать профессиональный, детальный промпт с нуля
3. Объяснить структуру созданного промпта

Форматируй ответ так:
**Анализ задачи:**
[Краткий анализ того, что нужно пользователю]

**Готовый промпт:**
```
[Профессиональный промпт, готовый к использованию]
```

**Структура промпта:**
[Объяснение каждого элемента промпта и почему он важен]

**Советы по использованию:**
[1-2 совета как лучше использовать этот промпт]

При создании промпта используй лучшие практики:
- Задавай роль для ИИ
- Определяй контекст и аудиторию
- Указывай формат и структуру ответа
- Добавляй конкретные требования и ограничения
- Включай примеры, если это улучшит результат

Будь полезным и образовательным. Отвечай на русском языке."""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = """Добро пожаловать в бот Промпт-Инженер!

Я создаю профессиональные промпты с нуля на основе твоего описания задачи.

Просто опиши, для чего тебе нужен промпт, и я:
- Проанализирую твою задачу
- Создам готовый к использованию промпт
- Объясню структуру и логику промпта

**Команды:**
/start - Показать это сообщение
/help - Как правильно описать задачу
/example - Посмотреть пример работы бота

**Как использовать:**
Напиши текстом или отправь голосовое сообщение. Например:
"Мне нужен промпт для создания поста в Instagram про путешествия"
"Хочу промпт для написания продающего текста"
"Нужен промпт для генерации идей для стартапа"

Опиши свою задачу текстом или голосом — я создам для тебя промпт!"""
    await update.message.reply_text(welcome_message)


async def help_command(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """**Как описать задачу для лучшего результата:**

1. **Укажи цель** - Что должен делать промпт?
   Пример: "для написания постов в соцсети"

2. **Добавь контекст** - О чём или для кого?
   Пример: "про фитнес для начинающих"

3. **Уточни формат** - Какой результат ты ожидаешь?
   Пример: "короткий текст до 150 слов"

4. **Укажи стиль** - Какой тон нужен?
   Пример: "дружелюбный и мотивирующий"

**Примеры хороших описаний:**

"Мне нужен промпт для создания описаний товаров в интернет-магазине косметики"

"Хочу промпт для написания email-рассылки для IT-компании, тон профессиональный"

"Нужен промпт для генерации идей контента для YouTube канала про кулинарию"

Чем подробнее описание — тем лучше промпт!"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def example_command(update: Update,
                          context: ContextTypes.DEFAULT_TYPE) -> None:
    example_text = """**Пример работы бота:**

**Твоё описание:**
"Мне нужен промпт для создания поста в Instagram про мозаику"

**Что создаст бот:**

**Анализ задачи:**
Нужен промпт для создания визуально привлекательного поста про мозаику для Instagram.

**Готовый промпт:**
```
Ты опытный SMM-специалист и эксперт по искусству мозаики. Напиши пост для Instagram про мозаику.

Требования:
- Длина: 150-200 слов
- Начни с цепляющего вопроса или факта
- Расскажи интересный факт о мозаике
- Добавь призыв к действию
- Предложи 5-7 релевантных хештегов
- Тон: вдохновляющий и познавательный

Формат:
[Основной текст]
—
[Хештеги]
```

**Структура промпта:**
- Роль: задаёт экспертизу
- Требования: конкретные параметры
- Формат: структурирует вывод

Опиши свою задачу — создам промпт для тебя!"""
    await update.message.reply_text(example_text, parse_mode='Markdown')


async def create_prompt(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> None:
    global openai_client
    user_task = update.message.text

    if not user_task or len(user_task.strip()) < 5:
        await update.message.reply_text("Пожалуйста, опиши задачу подробнее.")
        return

    await update.message.reply_text("Создаю промпт для твоей задачи...")

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": SYSTEM_PROMPT
            }, {
                "role":
                "user",
                "content":
                f"Создай профессиональный промпт для следующей задачи:\n\n{user_task}"
            }],
            max_completion_tokens=1024)

        result = response.choices[0].message.content

        if len(result) > 4000:
            result = result[:4000] + "...\n\n(Ответ сокращён из-за длины)"

        await update.message.reply_text(result, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error creating prompt: {e}", exc_info=True)
        await update.message.reply_text(
            "Извини, произошла ошибка при создании промпта. Попробуй ещё раз.")


async def handle_voice(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Распознаю голосовое сообщение...")

    try:
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)

        with tempfile.NamedTemporaryFile(suffix=".ogg",
                                         delete=False) as temp_file:
            temp_path = temp_file.name
            await voice_file.download_to_drive(temp_path)

        try:
            with open(temp_path, "rb") as audio_file:
                transcription = openai_client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file)

            transcribed_text = transcription.text

            if not transcribed_text or len(transcribed_text.strip()) < 5:
                await update.message.reply_text(
                    "Не удалось распознать текст. Попробуй записать ещё раз или напиши текстом."
                )
                return

            await update.message.reply_text(
                f"Распознано: {transcribed_text}\n\nСоздаю промпт...")

            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }, {
                    "role":
                    "user",
                    "content":
                    f"Создай профессиональный промпт для следующей задачи:\n\n{transcribed_text}"
                }],
                max_completion_tokens=1024)

            result = response.choices[0].message.content

            if len(result) > 4000:
                result = result[:4000] + "...\n\n(Ответ сокращён из-за длины)"

            await update.message.reply_text(result, parse_mode='Markdown')

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        await update.message.reply_text(
            "Извини, не удалось распознать голосовое сообщение. Попробуй записать ещё раз или напиши текстом."
        )


async def error_handler(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")


def main() -> None:
    global openai_client

    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        print("Ошибка: Установите переменную окружения TELEGRAM_BOT_TOKEN")
        return

    if not openai_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        print("Ошибка: Установите переменную окружения OPENAI_API_KEY")
        return

    # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
    # do not change this unless explicitly requested by the user
    openai_client = OpenAI(api_key=openai_key)

    application = Application.builder().token(telegram_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("example", example_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, create_prompt))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    application.add_error_handler(error_handler)

    logger.info("Бот успешно запущен!")
    print("Бот Промпт-Инженер запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
