from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, PreCheckoutQueryHandler
from words_declension import num_with_week, num_with_month, num_with_ruble
from db_helpers import get_entity_price
from bot_helpers import build_menu

GET_ENTITY_ORDER, GET_ENTITY_CONFIRMATION = range(40, 42)


def entity_greetings(update, context):

    keyboard = [
        [
            KeyboardButton('Хранение документов (890 руб./мес.)'),
        ],
        [
            KeyboardButton('Назад ⬅')
        ]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        'Наша компания готова предоставить Вашей организации следующие услуги:\n'
        'Аренда стеллажей для документов',
        reply_markup=reply_markup
    )

    return GET_ENTITY_ORDER


def entity_order(update, context):

    if update.message.text != 'Назад ⬅':
        context.user_data['supertype'] = update.message.text

    price = get_entity_price()

    time_buttons = [
        KeyboardButton(f'{time+1} мес.\n'
                       f'({(time+1) * price} руб.)')
        for time in range(12)
    ]

    time_buttons.append(KeyboardButton('Назад ⬅'))
    keyboard = build_menu(time_buttons, n_cols=3)

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        'Выберите на какой срок вы хотите арендовать стеллаж для хранения документов',
        reply_markup=reply_markup
    )

    return GET_ENTITY_CONFIRMATION

