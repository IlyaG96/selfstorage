import logging
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from environs import Env


GET_ADDRESS, GET_ACCEPT = range(2)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def start(update, _):
    keyboard = [
        [
            KeyboardButton('Адрес 1'),
            KeyboardButton('Адрес 2'),
            KeyboardButton('Адрес 3'),
            KeyboardButton('Адрес 4')
        ]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard)

    update.message.reply_text(
        'Привет, я бот компании SafeStorage, который поможет вам оставить вещи в ячейке хранения.'
        'Выберите адрес, чтобы перейти к получения кода доступа к ячейке',
        reply_markup=reply_markup
    )

    return GET_ADDRESS


def get_agreement_accept(update, _):
    keyboard = [
        [
            KeyboardButton('Принимаю'),
            KeyboardButton('Отказываюсь')
        ]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard)

    update.message.reply_text(
        'Замечательный выбор! А теперь примите, пожалуйста, соглашение о передаче персональных данных. '
        'Иначе мы не сможем обработать ваши данные :(',
        reply_markup=reply_markup
    )

    return GET_ACCEPT


def accept_failure(update, _):
    keyboard = [
        [
            KeyboardButton('Начать')
        ]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard)

    update.message.reply_text(
        'Жаль, что вы отказались. Мы не можем забронировать вам место без согласия на обработку персональных данных. '
        'Нажмите "Начать", если вы захотите снова воспользоваться ботом.',
        reply_markup=reply_markup
    )

    return ConversationHandler.END


def accept_success(update, _):
    update.message.reply_text(
        'Замечательно, можем переходить к заполнению ваших данных. '
        'Но здесь мои возможности пока заканчиваются :(',
        reply_markup=ReplyKeyboardRemove()
    )


if __name__ == '__main__':
    env = Env()
    env.read_env()
    BOT_TOKEN = env('BOT_TOKEN')
    updater = Updater(token=BOT_TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(Filters.regex('^Начать$'), start)],
        states={
            GET_ADDRESS: [
                MessageHandler(Filters.regex('^Адрес [1|2|3|4]$'), get_agreement_accept)
            ],
            GET_ACCEPT: [
                MessageHandler(Filters.regex('^Принимаю$'), accept_success),
                MessageHandler(Filters.regex('^Отказываюсь$'), accept_failure),
            ],
        },
        fallbacks=[CommandHandler('start', start), MessageHandler(Filters.regex('^Начать$'), start)],
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()
