from telegram import KeyboardButton, ReplyKeyboardMarkup
from db_helpers import get_entity_price
from bot_helpers import build_menu
from words_declension import num_with_month, num_with_ruble
from payments import count_price

GET_ENTITY_ORDER, GET_ENTITY_COUNT, ENTITY_ORDER_CONFIRMATION = range(40, 43)
GET_PERSONAL_DATA = 4


def entity_greetings(update, context):

    if update.message.text != 'Назад ⬅':
        context.user_data['supertype'] = update.message.text

    buttons = [
            KeyboardButton('Аренда стеллажей для хранения документов (899 руб./мес.)'),
        ]

    keyboard = build_menu(buttons, n_cols=2, footer_buttons=[KeyboardButton('Назад ⬅')])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        'Наша компания готова предоставить Вашей организации следующие услуги:\n'
        'Аренда стеллажей для хранения документов',
        reply_markup=reply_markup
    )

    return GET_ENTITY_COUNT


def entity_count(update, context):

    if update.message.text != 'Назад ⬅':
        context.user_data['entity_service_type'] = update.message.text

    buttons = [
            KeyboardButton('Назад ⬅'),
        ]

    keyboard = build_menu(buttons, n_cols=2)
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        'Какое количество стеллажей Вы хотели бы арендовать?',
        reply_markup=reply_markup
    )

    return GET_ENTITY_ORDER


def entity_order(update, context):

    user_data = context.user_data
    if update.message.text != 'Назад ⬅':
        context.user_data['entity_rack_count'] = int(update.message.text)

    price = get_entity_price()
    count = user_data['entity_rack_count']
    time_buttons = [
        KeyboardButton(f'{time+1} мес.\n'
                       f'({(time+1) * price * count} руб.)')
        for time in range(12)
    ]

    keyboard = build_menu(time_buttons, n_cols=3, footer_buttons=[KeyboardButton('Назад ⬅')])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        'Выберите срок аренды:',
        reply_markup=reply_markup
    )

    return ENTITY_ORDER_CONFIRMATION


def entity_order_confirmation(update, context):

    keyboard = [
        [KeyboardButton('Подтвердить'), KeyboardButton('Назад ⬅')]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    user_data = context.user_data

    time = int(update.message.text.split(" ")[0])
    user_data['entity_time'] = time

    update.message.reply_text(
        f'Ваш заказ: \n'
        f'Тип: {user_data["supertype"]}\n'
        f'Количество стеллажей: {user_data["entity_rack_count"]}\n'
        f'Время хранения: {num_with_month(time)}\n'
        f'Итоговая цена: {num_with_ruble(count_price(update, context))}',
        reply_markup=reply_markup
    )

    return GET_PERSONAL_DATA


def entity_order_confirmation_back(update, context):
    if context.user_data['supertype'] == 'Услуги для юридических лиц':
        return entity_count(update, context)


def entity_order_back(update, context):
    if context.user_data['supertype'] == 'Услуги для юридических лиц':
        return entity_greetings(update, context)

