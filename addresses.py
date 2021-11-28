from geopy import Photon
from geopy.distance import distance
from telegram import KeyboardButton, ReplyKeyboardMarkup
from bot_helpers import build_menu
from db_helpers import get_warehouses_with_short_name, get_warehouse_coords_by_address, get_user

GET_ADDRESS, GET_ADDRESS_TYPE, GET_USER_LOCATION, GET_ADDRESS_WITH_LOCATION = range(30, 34)


def get_location_by_address(address):
    geocoder = Photon()
    result = geocoder.geocode(address)
    if result:
        return result.latitude, result.longitude
    else:
        return None


def get_address_type(update, _):
    user = get_user(update.message.from_user.id)
    if user:
        greeting = ''
    else:
        greeting = 'Привет, я бот компании SafeStorage, который поможет вам оставить вещи в ячейке хранения. '

    address_type_buttons = [
        [KeyboardButton('Да, подскажите'), KeyboardButton('Нет, выберу сам')]
    ]

    reply_markup = ReplyKeyboardMarkup(address_type_buttons, resize_keyboard=True)

    update.message.reply_text(
        f'{greeting}'
        'Перед тем, как перейти к бронированию, вам нужно выбрать адрес склада для хранения. '
        'Определить расстояние от складов до вас?',
        reply_markup=reply_markup
    )

    return GET_ADDRESS_TYPE


def get_address(update, context):
    context.user_data['is_located'] = False

    addresses = get_warehouses_with_short_name()

    addresses_buttons = [
        KeyboardButton(short_name) for address, short_name in addresses.items()
    ]

    keyboard = build_menu(addresses_buttons, n_cols=2, footer_buttons=[KeyboardButton('Назад ⬅')])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    text = 'Выберите адрес склада\n'

    for address, short_name in addresses.items():
        text += f'{short_name} - {address}\n'

    update.message.reply_text(
        text,
        reply_markup=reply_markup
    )
    return GET_ADDRESS


def get_address_with_location(update, context):
    if update.message.location:
        user_location = (
            update.message.location['latitude'], update.message.location['longitude']
        )
        context.user_data['location'] = user_location
    elif update.message.text != 'Назад ⬅':
        user_location = get_location_by_address(update.message.text)
        context.user_data['location'] = user_location
        if not user_location:
            update.message.reply_text(
                'Адрес некорректен. Проверьте то, что вы ввели, или отправьте гео-точку'
            )
            return GET_USER_LOCATION
    else:
        user_location = context.user_data['location']

    addresses_with_shortnames = get_warehouses_with_short_name()

    formatted_addresses = [
        f'{shortname}\n({round(distance(user_location, get_warehouse_coords_by_address(address)).km)} км)'
        for address, shortname in addresses_with_shortnames.items()
    ]

    addresses_buttons = [KeyboardButton(address) for address in formatted_addresses]

    keyboard = build_menu(addresses_buttons, n_cols=2, footer_buttons=[KeyboardButton('Назад ⬅')])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    text = 'Выберите адрес склада\n'

    for address, short_name in addresses_with_shortnames.items():
        text += f'{short_name} - {address}\n'

    update.message.reply_text(
        text,
        reply_markup=reply_markup
    )
    return GET_ADDRESS_WITH_LOCATION


def get_user_location(update, context):
    context.user_data['is_located'] = True

    user_location_buttons = [
        [KeyboardButton('Отправить мое местоположение', request_location=True), KeyboardButton('Назад ⬅')]
    ]

    reply_markup = ReplyKeyboardMarkup(user_location_buttons, resize_keyboard=True)

    update.message.reply_text(
        'Напишите свой адрес или нажмите кнопку, чтобы отправить свое местоположение',
        reply_markup=reply_markup
    )

    return GET_USER_LOCATION
