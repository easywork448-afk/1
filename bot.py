import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv
from typing import Any
import asyncio

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token and target group ID from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
TARGET_GROUP_ID = os.getenv('TARGET_GROUP_ID')

# Store user states for conversation handling
USER_STATES = {}

# Store message mappings to track which user message corresponds to which group message
MESSAGE_MAPPING: dict[int, int] = {}  # {group_message_id: user_chat_id}
# Track last sent group message per user chat to allow deletion when a new message arrives
LAST_GROUP_MESSAGE_BY_USER: dict[int, int] = {}  # {user_chat_id: group_message_id}
# Track last bot message per chat (welcome/help menus) to replace them when updated
LAST_BOT_MESSAGE_BY_CHAT: dict[int, int] = {}

# Anonymous mode settings
ANONYMOUS_MODE = True  # Set to False to show real usernames

# TGK bot integration
TGK_BOT_USERNAME = "uidowq"  # TGK bot username for forwarding
CHANNEL_URL = f"https://t.me/{TGK_BOT_USERNAME}"

# Custom emojis for better UX
EMOJI_SENDING = '✈️'
EMOJI_SUCCESS = '✅'
EMOJI_ERROR = '❌'
EMOJI_HOME = '🏠'
EMOJI_BACK = '🔙'

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "Ⳅⲇⲣⲁⲃⲥⲧⲃⲩύ, ⲡⲩⲧⲏυⲕ… ✨\n"
        "Ты ⳅⲁⲅⲗяⲏⲩⲗ ⲧⲩⲇⲁ, ⲅⲇⲉ ⲃⲥⲉⲅⲇⲁ ⲧⲉⲡⲗⲟ υ ⲡⲟⲏяⲧⲏⲟ 🌙\n"
        "Ⲧⲉⳝⲉ ⲥⲕⲩⳡⲏⲟ?\n"
        "Ⲏⲉⲕⲟⲙⲩ ⲃыⲅⲟⲃⲟⲣυⲧьⲥя?\n"
        "Ⲏⲩⲯⲏⲁ ⲡⲟⲇⲇⲉⲣⲯⲕⲁ υⲗυ ⲡⲣⲟⲥⲧⲟ ⲣⲁⳅⲅⲟⲃⲟⲣ? 💭\n"
        "Ⲙы ⲣяⲇⲟⲙ.\n"
        "Ⲡυⲱυ ⲏⲁⲙ — υ ⲧⲣ ⲏⲉ ⲟⲥⲧⲁⲏⲉⲱьⲥя ⲟⲇυⲏ 🤍\n"
        "Ⲏⲁⲱ ⳝⲟⲧ — эⲧⲟ ⲙⲉⲥⲧⲟ, ⲅⲇⲉ:\n"
        "✦ ⲥⲗⲩⲱⲁюⲧ\n"
        "✦ ⲡⲟⲇⲇⲉⲣⲯυⲃⲁюⲧ\n"
        "✦ ⲟⲧⲃⲉⳡⲁюⲧ ⲃⲥⲉⲅⲇⲁ\n"
        "Ⲁ ⲉⳃё… 🌌\n"
        "Ⲙы υⳃⲉⲙ ⲏⲟⲃыⲉ ⳅⲃёⳅⲇы ⲃ ⲏⲁⲱⲉⲙ ⲏⲉⳝⲉ ✨\n"
        "Ⲏⲩⲯⲏы:\n"
        "ⲁⲇⲙυⲏы\n"
        "ⲙⲟⲏⲧⲁⲯёⲣы\n"
        "ⲡⲟⲙⲟⳃⲏυⲕυ ⲡⲟ ⲡⲟⲥⲧⲁⲙ υ ⲃυⲇⲉⲟ\n"
        "Ⲉⲥⲗυ ⲧы ⳡⲩⲃⲥⲧⲃⲩⲉⲱь, ⳡⲧⲟ эⲧⲟ ⲡⲣⲟ ⲧⲉⳝя —\n"
        "ⲡυⲱυ. Ⲙы ⲧⲉⳝя ⲯⲇёⲙ 🌑💫"
    )
    
    # Send welcome message with a nice menu
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI_SENDING} Отправить сообщение", callback_data='send_message')],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')],
        [InlineKeyboardButton("🔗 Канал бота", url=CHANNEL_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # If it's a callback query, edit the message, otherwise send a new one
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        # delete the old message (if possible) to avoid showing stale text
        try:
            if query.message:
                await query.message.delete()
        except Exception:
            pass
        sent = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        try:
            LAST_BOT_MESSAGE_BY_CHAT[update.effective_chat.id] = sent.message_id
        except Exception:
            pass
    else:
        # remove previous bot menu in this chat if exists
        try:
            prev = LAST_BOT_MESSAGE_BY_CHAT.get(update.effective_chat.id)
            if prev:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prev)
        except Exception:
            pass
        sent = await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        try:
            LAST_BOT_MESSAGE_BY_CHAT[update.effective_chat.id] = sent.message_id
        except Exception:
            pass

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "📚 <b>Справка по боту</b>\n\n"
        "Этот бот пересылает сообщения в целевую группу.\n\n"
        "<b>Как использовать:</b>\n"
        "1. Просто отправь мне любое сообщение (текст, фото, видео, документ и т.д.)\n"
        "2. Я перешлю его в целевую группу\n\n"
        "<b>Команды:</b>\n"
        "/start - Начать работу\n"
        "/help - Показать эту справку\n"
        "/send - Отправить новое сообщение"
    )
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI_BACK} Назад", callback_data='back_to_start')],
        [InlineKeyboardButton(f"{EMOJI_SENDING} Отправить сообщение", callback_data='send_message')],
        [InlineKeyboardButton("🔗 Канал бота", url=CHANNEL_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=help_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def send_message_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt the user to send a message to forward."""
    query = update.callback_query
    if query:
        await query.answer()
    
    prompt_text = (
        "📝 <b>Отправьте сообщение для пересылки</b>\n\n"
        "Вы можете отправить:\n"
        "• Текст\n"
        "• Фотографии\n"
        "• Видео\n"
        "• Документы\n"
        "• Голосовые сообщения\n\n"
        "Я перешлю его в целевую группу."
    )
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI_BACK} Отмена", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(
            text=prompt_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    elif update.message:
        await update.message.reply_text(
            prompt_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    # Set user state to waiting for message
    USER_STATES[update.effective_user.id] = 'waiting_for_message'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and forward them to the target group."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if user is in the waiting state or sending a direct message
    if USER_STATES.get(user.id) == 'waiting_for_message' or chat.type == 'private':
        # Send typing action for better UX
        await context.bot.send_chat_action(
            chat_id=chat.id,
            action='typing'
        )
        
        try:
            # Forward the message to the target group (use copy_message to avoid "Переслано от")
            author_label = ""
            if not ANONYMOUS_MODE:
                name = f"@{user.username}" if user.username else user.first_name
                author_label = f" от {name}"

            if update.message.text:
                # For text messages
                sent_message = await context.bot.send_message(
                    chat_id=TARGET_GROUP_ID,
                    text=f"📩 <b>Новое сообщение{author_label}:</b>\n\n{update.message.text}",
                    parse_mode='HTML'
                )
            elif update.message.photo:
                # For photos: copy if anonymous, otherwise send with author label
                if ANONYMOUS_MODE:
                    sent_message = await context.bot.copy_message(
                        chat_id=TARGET_GROUP_ID,
                        from_chat_id=chat.id,
                        message_id=update.message.message_id
                    )
                else:
                    photo = update.message.photo[-1]
                    sent_message = await context.bot.send_photo(
                        chat_id=TARGET_GROUP_ID,
                        photo=photo.file_id,
                        caption=f"📸 <b>Фото{author_label}</b>\n\n{update.message.caption or ''}",
                        parse_mode='HTML'
                    )
            elif update.message.video:
                if ANONYMOUS_MODE:
                    sent_message = await context.bot.copy_message(
                        chat_id=TARGET_GROUP_ID,
                        from_chat_id=chat.id,
                        message_id=update.message.message_id
                    )
                else:
                    sent_message = await context.bot.send_video(
                        chat_id=TARGET_GROUP_ID,
                        video=update.message.video.file_id,
                        caption=f"🎥 <b>Видео{author_label}</b>\n\n{update.message.caption or ''}",
                        parse_mode='HTML'
                    )
            elif update.message.document:
                if ANONYMOUS_MODE:
                    sent_message = await context.bot.copy_message(
                        chat_id=TARGET_GROUP_ID,
                        from_chat_id=chat.id,
                        message_id=update.message.message_id
                    )
                else:
                    sent_message = await context.bot.send_document(
                        chat_id=TARGET_GROUP_ID,
                        document=update.message.document.file_id,
                        caption=f"📄 <b>Документ{author_label}</b>\n\n{update.message.caption or ''}",
                        parse_mode='HTML'
                    )
            else:
                # For other message types, copy (preserves content without 'forwarded from')
                sent_message = await context.bot.copy_message(
                    chat_id=TARGET_GROUP_ID,
                    from_chat_id=chat.id,
                    message_id=update.message.message_id
                )

            # If we get here, the message was sent successfully
            channel_button = InlineKeyboardButton("🔗 Канал бота", url=CHANNEL_URL)
            await update.message.reply_text(
                f"{EMOJI_SUCCESS} Сообщение успешно отправлено в группу!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"{EMOJI_HOME} В главное меню", callback_data='back_to_start')],
                    [InlineKeyboardButton(f"{EMOJI_SENDING} Отправить ещё", callback_data='send_message')],
                    [channel_button]
                ])
            )

            # Delete previous message from this user in the group to avoid clutter
            try:
                prev_group_msg_id = LAST_GROUP_MESSAGE_BY_USER.get(chat.id)
                if prev_group_msg_id:
                    await context.bot.delete_message(chat_id=TARGET_GROUP_ID, message_id=prev_group_msg_id)
                    # remove its reverse mapping if present
                    if prev_group_msg_id in MESSAGE_MAPPING:
                        del MESSAGE_MAPPING[prev_group_msg_id]
            except Exception:
                # ignore delete errors
                pass

            # Store the mapping between group message and user chat
            MESSAGE_MAPPING[sent_message.message_id] = chat.id
            LAST_GROUP_MESSAGE_BY_USER[chat.id] = sent_message.message_id

            # Reset user state
            if user.id in USER_STATES:
                del USER_STATES[user.id]
                
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            await update.message.reply_text(
                f"{EMOJI_ERROR} Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте снова.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"{EMOJI_BACK} Назад", callback_data='back_to_start')]
                ])
            )
    else:
        # If not in private chat and not in waiting state, show start menu
        await start(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses from inline keyboards."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_start':
        if update.effective_user.id in USER_STATES:
            del USER_STATES[update.effective_user.id]
        await start(update, context)
    elif query.data == 'help':
        await help_command(update, context)
    elif query.data == 'send_message':
        await send_message_prompt(update, context)


async def _is_user_admin_in_chat(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ('administrator', 'creator')
    except Exception:
        return False


async def anon_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enable anonymous mode from inside the target group (admins only)."""
    chat = update.effective_chat
    if not _is_target_group(chat):
        await update.message.reply_text("Эту команду нужно выполнять в целевой группе.")
        return
    is_admin = await _is_user_admin_in_chat(chat.id, update.effective_user.id, context)
    if not is_admin:
        await update.message.reply_text("Только админы могут менять настройки анонимности.")
        return
    global ANONYMOUS_MODE
    ANONYMOUS_MODE = True
    await update.message.reply_text("Анонимный режим включён. Отправители скрыты.")


async def anon_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Disable anonymous mode from inside the target group (admins only)."""
    chat = update.effective_chat
    if not _is_target_group(chat):
        await update.message.reply_text("Эту команду нужно выполнять в целевой группе.")
        return
    is_admin = await _is_user_admin_in_chat(chat.id, update.effective_user.id, context)
    if not is_admin:
        await update.message.reply_text("Только админы могут менять настройки анонимности.")
        return
    global ANONYMOUS_MODE
    ANONYMOUS_MODE = False
    await update.message.reply_text("Анонимный режим выключен. Отправители будут подписываться.")


def _is_target_group(chat: Any) -> bool:
    if not chat:
        return False
    if not TARGET_GROUP_ID:
        return False
    # TARGET_GROUP_ID can be numeric (e.g. -100...) or @username
    if isinstance(TARGET_GROUP_ID, str) and TARGET_GROUP_ID.startswith('@'):
        return bool(chat.username) and f"@{chat.username}" == TARGET_GROUP_ID
    try:
        return int(TARGET_GROUP_ID) == int(chat.id)
    except Exception:
        return False


async def handle_group_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """If staff replies in the support group, forward the reply back to the original user."""
    if not update.message:
        return

    chat = update.effective_chat
    if not _is_target_group(chat):
        return

    if not update.message.reply_to_message:
        return

    replied_to_id = update.message.reply_to_message.message_id
    user_chat_id = MESSAGE_MAPPING.get(replied_to_id)
    if not user_chat_id:
        return

    # Send back the staff reply to the user
    try:
        await update.message.copy(chat_id=user_chat_id)
    except Exception as e:
        logger.error(f"Error sending group reply back to user: {e}")

def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("No BOT_TOKEN found in environment variables")
        print("Ошибка: Не найден BOT_TOKEN в переменных окружения.")
        print("Пожалуйста, создайте файл .env и добавьте в него BOT_TOKEN=ваш_токен")
        return
    
    if not TARGET_GROUP_ID:
        logger.error("No TARGET_GROUP_ID found in environment variables")
        print("Ошибка: Не найден TARGET_GROUP_ID в переменных окружения.")
        print("Пожалуйста, создайте файл .env и добавьте в него TARGET_GROUP_ID=@ваша_группа")
        return
    
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("send", send_message_prompt))
    
    # Add callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_handler))
    # Group admin commands to toggle anonymous mode (should be used in the target group)
    application.add_handler(CommandHandler("anon_on", anon_on))
    application.add_handler(CommandHandler("anon_off", anon_off))
    
    # Private user messages -> forward to group
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_message))

    # Replies in support group -> forward back to user
    application.add_handler(MessageHandler((filters.ChatType.GROUP | filters.ChatType.SUPERGROUP) & filters.REPLY & ~filters.COMMAND, handle_group_reply))

    # Start the Bot
    print("Бот запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling()

if __name__ == '__main__':
    main()
