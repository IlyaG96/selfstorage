from telegram import KeyboardButton, ReplyKeyboardMarkup
from bot_helpers import build_menu


GET_ADDRESS, GET_ADDRESS_TYPE, GET_USER_LOCATION = range(30, 33)


def get_distance(place1, place2, /):
    distance = None
    return distance


def get_address_type(update, _):
    address_type_buttons = [
        [KeyboardButton('Да, подскажите'), KeyboardButton('Нет, выберу сам')]
    ]

    reply_markup = ReplyKeyboardMarkup(address_type_buttons, resize_keyboard=True)

    update.message.reply_text(
        'Привет, я бот компании SafeStorage, который поможет вам оставить вещи в ячейке хранения. '
        'Перед тем, как перейти к бронированию, вам нужно выбрать адрес склада для хранения. '
        'Определить расстояние от складов до вас?',
        reply_markup=reply_markup
    )

    return GET_ADDRESS_TYPE


def get_address(update, _):
    # replace with get from db
    addresses = [
        'Рязанский пр., 16 строение 4',
        'ул. Наташи Ковшовой, 2',
        'Люблинская ул., 60 корпус 2',
        'Походный пр-д, 6'
    ]

    addresses_buttons = [
        KeyboardButton(address) for address in addresses
    ]

    keyboard = build_menu(addresses_buttons, n_cols=2)

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        'Выберите адрес склада',
        reply_markup=reply_markup
    )
    return GET_ADDRESS


def get_address_with_location(update, _):


    # replace with get from db
    addresses = [
        'Рязанский пр., 16 строение 4',
        'ул. Наташи Ковшовой, 2',
        'Люблинская ул., 60 корпус 2',
        'Походный пр-д, 6'
    ]

    city = 'Москва'  # for future usage

    prefixed_addresses = [f'Россия, {city}, {address}' for address in addresses]

    addresses_buttons = [
        KeyboardButton(address) for address in addresses
    ]

    keyboard = build_menu(addresses_buttons, n_cols=2)

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        'Выберите адрес склада',
        reply_markup=reply_markup
    )
    return GET_ADDRESS


def get_user_location(update, _):
    user_location_buttons = [
        [KeyboardButton('Отправить мое местоположение', request_location=True), KeyboardButton('Назад ⬅')]
    ]

    reply_markup = ReplyKeyboardMarkup(user_location_buttons, resize_keyboard=True)

    update.message.reply_text(
        'Напишите свой адрес или нажмите кнопку, чтобы отправить свое местоположение',
        reply_markup=reply_markup
    )

    return GET_USER_LOCATION
