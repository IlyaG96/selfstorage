import logging
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from environs import Env


GET_ADDRESS, GET_ACCEPT, GET_THINGS_TYPE, GET_OTHER_THINGS_AREA, GET_OTHER_THINGS_TIME = range(6)


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


def get_things_type(update, _):
    keyboard = [
        [
            KeyboardButton('Сезонные вещи'),
            KeyboardButton('Другое')
        ]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard)

    update.message.reply_text(
        'Теперь выберите, пожалуйста, тип вещей для хранения',
        reply_markup=reply_markup
    )

    return GET_THINGS_TYPE


def get_other_things_area(update, _):
    # replace with get from db
    start_price = 599
    add_price = 150

    things_areas_buttons = [
        [KeyboardButton(f'{area + 1} кв.м за {start_price + add_price * area} рублей в месяц')] for area in range(0, 10)
    ]

    reply_markup = ReplyKeyboardMarkup(things_areas_buttons)

    update.message.reply_text(
        'Выберите площадь необходимую для хранения ваших вещей',
        reply_markup=reply_markup
    )

    return GET_OTHER_THINGS_AREA


def get_other_things_time(update, _):
    time_buttons = [
        [KeyboardButton(f'На {time} месяцев')] for time in range(1, 13)
    ]

    reply_markup = ReplyKeyboardMarkup(time_buttons)

    update.message.reply_text(
        'Выберите на какой срок вы хотите снять ячейку хранения',
        reply_markup=reply_markup
    )

    return GET_OTHER_THINGS_TIME


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
                MessageHandler(Filters.regex('^Адрес [1|2|3|4]$'), get_things_type)
            ],
            GET_THINGS_TYPE: [
                MessageHandler(Filters.regex('^Другое$'), get_other_things_area)
            ],
            GET_OTHER_THINGS_AREA: [
                MessageHandler(Filters.regex(r'^\d{1,2} кв\.м за \d{3,4} рублей в месяц$'), get_other_things_time)
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
