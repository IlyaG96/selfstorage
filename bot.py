import logging
import re
from pathlib import Path

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, PreCheckoutQueryHandler
from environs import Env

from addresses import get_address, get_address_type, get_user_location, get_address_with_location, \
    GET_ADDRESS, GET_ADDRESS_TYPE, GET_USER_LOCATION, GET_ADDRESS_WITH_LOCATION
from bot_helpers import build_menu, check_age
from words_declension import num_with_week, num_with_month, num_with_ruble
from db_helpers import add_user, get_user, get_code, create_db, selfstorage, add_prices, add_reservation, \
    get_reservations, get_other_prices, get_seasoned_prices, get_seasoned_things, add_warehouses, \
    get_warehouses_with_short_name, get_warehouse_id_by_short_name
from payments import take_payment, count_price, precheckout, check_promocode, PRECHECKOUT, SUCCESS_PAYMENT, TAKE_PAYMENT
from entity_services import entity_greetings, entity_order, entity_count, entity_order_confirmation, \
    entity_order_confirmation_back, entity_order_back, GET_ENTITY_ORDER, GET_ENTITY_COUNT, ENTITY_ORDER_CONFIRMATION
GET_ACCEPT, GET_THINGS_TYPE, GET_OTHER_THINGS_AREA, GET_THINGS_CONFIRMATION, GET_PERSONAL_DATA = range(5)
GET_SEASONED_THINGS_TYPE, GET_SEASONED_THINGS_COUNT, GET_SEASONED_THINGS_TIME_TYPE = range(5, 8)
GET_NAME_INPUT_CHOICE, GET_PATRONYMIC, GET_FULL_NAME = range(8, 11)
GET_PHONE, GET_PASSPORT, GET_BIRTHDATE, GET_PAYMENT_ACCEPT, GET_USER_CHOICE, GET_SHOW_THINGS_CHOICE, GET_PROMOCODE = range(11, 18)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def start(update, context):
    user = get_user(update.message.from_user.id)
    context.user_data['user_id'] = update.message.from_user.id
    if user:
        reply_keyboard = [['Забронировать место', 'Вещи на хранении']]
        update.message.reply_text(
            'Рад вас снова видеть!',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                resize_keyboard=True,
            )
        )
        return GET_USER_CHOICE
    else:
        return get_address_type(update, context)


def get_things_type(update, context):
    if update.message.text != 'Назад ⬅':
        addresses = get_warehouses_with_short_name()
        short_names = tuple(addresses.values())

        for short_name in short_names:
            if update.message.text.startswith(short_name):
                context.user_data['warehouse_id'] = get_warehouse_id_by_short_name(short_name)
                break
        else:
            return GET_ADDRESS

    buttons = [
            KeyboardButton('Сезонные вещи'),
            KeyboardButton('Другое'),
            KeyboardButton('Услуги для юридических лиц')
        ]
    keyboard = build_menu(buttons, n_cols=2, footer_buttons=[KeyboardButton('Назад ⬅')])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        'Теперь выберите, пожалуйста, тип вещей для хранения или тип услуг',
        reply_markup=reply_markup
    )

    return GET_THINGS_TYPE


def get_other_things_area(update, context):
    if update.message.text != 'Назад ⬅':
        context.user_data['supertype'] = update.message.text

    start_price, add_price = get_other_prices()

    things_areas_buttons = [KeyboardButton(f'{area + 1} м² за {start_price + add_price * area} руб./мес.')
                            for area in range(1, 11)]
    things_areas_buttons.append(KeyboardButton('Назад ⬅'))

    things_areas_menu = build_menu(things_areas_buttons, n_cols=3)

    reply_markup = ReplyKeyboardMarkup(things_areas_menu, resize_keyboard=True)

    update.message.reply_text(
        'Выберите площадь, необходимую для хранения ваших вещей',
        reply_markup=reply_markup
    )

    return GET_OTHER_THINGS_AREA


def get_other_things_time(update, context):
    if update.message.text != 'Назад ⬅':
        area = re.match(r'^(\d{1,2}) м² за \d{3,4} руб./мес.$', update.message.text).groups()[0]

        context.user_data['other_area'] = int(area)

    time_buttons = [
        KeyboardButton(f'{time} мес.')
        for time in range(1, 13)
    ]
    time_buttons.append(KeyboardButton('Назад ⬅'))

    time_menu = build_menu(time_buttons, n_cols=3)

    reply_markup = ReplyKeyboardMarkup(time_menu, resize_keyboard=True)

    update.message.reply_text(
        'Выберите на какой срок вы хотите снять ячейку хранения',
        reply_markup=reply_markup
    )

    return GET_THINGS_CONFIRMATION


def get_seasoned_things_type(update, context):
    if update.message.text != 'Назад ⬅':
        context.user_data['supertype'] = update.message.text

    things_types = get_seasoned_things()

    things_types_buttons = [
        KeyboardButton(things_types[i]) for i in range(0, 4)
    ]

    things_types_menu = build_menu(things_types_buttons, n_cols=2, footer_buttons=[KeyboardButton('Назад ⬅')])

    reply_markup = ReplyKeyboardMarkup(things_types_menu, resize_keyboard=True)

    update.message.reply_text(
        'Выберите вещь, которую будете хранить',
        reply_markup=reply_markup
    )

    return GET_SEASONED_THINGS_TYPE


def get_seasoned_things_count(update, context):
    if update.message.text != 'Назад ⬅':
        things_types = get_seasoned_things()

        if update.message.text in things_types:
            context.user_data['seasoned_type'] = update.message.text
        else:
            return GET_SEASONED_THINGS_TYPE

    update.message.reply_text(
        'Напишите количество вещей',
        reply_markup=ReplyKeyboardMarkup([['Назад ⬅']], resize_keyboard=True)
    )

    return GET_SEASONED_THINGS_COUNT


def get_seasoned_things_time_type(update, context):
    user_data = context.user_data
    if update.message.text != 'Назад ⬅':
        user_data['seasoned_count'] = int(update.message.text)

    buttons = [
            KeyboardButton(f'Недели'),
            KeyboardButton(f'Месяцы')
        ]

    keyboard = build_menu(buttons, n_cols=2, footer_buttons=[KeyboardButton('Назад ⬅')])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text('Вы хотите снять ячейку хранения на 1-3 недели или несколько месяцев?',
                              reply_markup=reply_markup)

    return GET_SEASONED_THINGS_TIME_TYPE


def get_seasoned_things_time(update, context):
    user_data = context.user_data

    if update.message.text != 'Назад ⬅' and update.message.text.startswith(('Месяцы', 'Недели')):
        user_data['seasoned_time_type'] = 'month' if update.message.text.startswith('Месяцы') else 'week'
    time_type = user_data['seasoned_time_type']

    things_price = get_seasoned_prices()
    thing = user_data['seasoned_type']
    price = things_price.get(thing)
    week_price, month_price = price
    count = user_data['seasoned_count']

    if time_type == 'week':
        time_buttons = [
            KeyboardButton(f'{time+1} нед.\n'
                           f'({(time+1) * week_price * count} руб.)')
            for time in range(3)
        ]
    else:
        time_buttons = [
            KeyboardButton(f'{time + 1} мес.\n'
                           f'({(time + 1) * month_price * count} руб.)')
            for time in range(6)
        ]

    time_buttons.append(KeyboardButton('Назад ⬅'))

    time_menu = build_menu(time_buttons, n_cols=3)

    reply_markup = ReplyKeyboardMarkup(time_menu, resize_keyboard=True)

    update.message.reply_text(
        'Выберите на какой срок вы хотите снять ячейку хранения',
        reply_markup=reply_markup
    )

    return GET_THINGS_CONFIRMATION


def get_things_confirmation(update, context):
    keyboard = [
        [KeyboardButton('Подтвердить'), KeyboardButton('Назад ⬅')]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    user_data = context.user_data

    if user_data['supertype'] == 'Другое':
        time = re.match(r'^(\d{1,2}) мес.$', update.message.text).groups()[0]
        user_data['other_time'] = int(time)

        update.message.reply_text(
            f'Ваш заказ: \n'
            f'Тип: {user_data["supertype"]}\n'
            f'Площадь: {user_data["other_area"]} м²\n'
            f'Время хранения: {num_with_month(user_data["other_time"])}\n'
            f'Итоговая цена: {num_with_ruble(count_price(update, context))}',
            reply_markup=reply_markup
        )
    elif user_data['supertype'] == 'Сезонные вещи':
        if 'нед' in update.message.text:
            time = int(re.match(r'^(\d) нед\.\n\(\d{2,5} руб\.\)$', update.message.text).groups()[0])
        elif 'мес' in update.message.text:
            time = int(re.match(r'^(\d) мес\.\n\(\d{2,5} руб\.\)$', update.message.text).groups()[0])

        user_data['seasoned_time'] = time
        time_type = user_data['seasoned_time_type']

        update.message.reply_text(
            f'Ваш заказ: \n'
            f'Тип: {user_data["seasoned_type"]}\n'
            f'Количество: {user_data["seasoned_count"]}\n'
            f'Время хранения: {num_with_week(time) if time_type == "week" else num_with_month(time)}\n'
            f'Итоговая цена: {num_with_ruble(count_price(update, context))}',
            reply_markup=reply_markup
        )

    return GET_PERSONAL_DATA


def get_promocode(update, context):
    update.message.reply_text(
        'Введите промокод',
        reply_markup=ReplyKeyboardMarkup(
            [['Пропустить']],
            resize_keyboard=True,
        ),
    )
    return GET_PROMOCODE  


def get_agreement_accept(update, context):
    coefficient, message = check_promocode(update.message.text, context.user_data)
    user = get_user(update.message.from_user.id)
    if user:
        total_price = int(count_price(update, context) * coefficient)
        context.user_data['cost'] = total_price
    
        update.message.reply_text(
            f'{message}Стоимость бронирования: {total_price} руб.',
            reply_markup=ReplyKeyboardMarkup(
                [['Оплатить']],
                resize_keyboard=True,
            ),
        )
        return TAKE_PAYMENT
    else:
        keyboard = [
            [
                KeyboardButton('Принимаю'),
                KeyboardButton('Отказываюсь')
            ]
        ]
    
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
        update.message.reply_text(
            'Примите соглашение об обработке персональных данных',
            reply_markup=reply_markup
        )
        with open('pd_processing_agreement.pdf', 'rb') as pd_file:
            update.message.reply_document(pd_file)
    
        return GET_ACCEPT


def accept_failure(update, _):
    keyboard = [
        [
            KeyboardButton('Принимаю'),
            KeyboardButton('Отказываюсь')
        ]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        'К сожалению, без согласия на обработку данных вы не сможете забронировать у нас место',
        reply_markup=reply_markup
    )

    return GET_ACCEPT


def name_from_contact(update, _):
    user = update.message.from_user
    first_name = user.first_name
    last_name = user.last_name
    if first_name and last_name:
        reply_keyboard = [
            ['Добавить отчество', 'Ввести ФИО'],
            ['Пропустить'],
        ]
        update.message.reply_text(
            f'Фамилия и имя взятые из вашего профиля:\n'
            f'{last_name} {first_name}\n\n'
            f'Добавьте отчество или введите корректные ФИО полностью\n',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                resize_keyboard=True,
            )
        )
        return GET_NAME_INPUT_CHOICE
    else:
        update.message.reply_text(
            'Введите ФИО полностью',
            reply_markup=ReplyKeyboardRemove()
        )
        return GET_FULL_NAME


def patronymic(update, context):
    user = update.message.from_user
    context.user_data['first_name'] = user.first_name
    context.user_data['last_name'] = user.last_name
    update.message.reply_text(
        'Введите отчество',
        reply_markup=ReplyKeyboardRemove()
    )
    return GET_PATRONYMIC


def full_name(update, _):
    update.message.reply_text(
        'Введите ФИО полностью',
        reply_markup=ReplyKeyboardRemove()
    )
    return GET_FULL_NAME


def phone(update, context):
    if update.message.text == 'Пропустить':
        user = update.message.from_user
        context.user_data['first_name'] = user.first_name
        context.user_data['last_name'] = user.last_name
        context.user_data['patronymic'] = None
    else:
        message_parts = update.message.text.split()
        if len(message_parts) == 3:
            last_name, first_name, patronymic = message_parts
            context.user_data['last_name'] = last_name
            context.user_data['first_name'] = first_name
            context.user_data['patronymic'] = patronymic
        elif len(message_parts) == 2:
            last_name, first_name = message_parts
            context.user_data['last_name'] = last_name
            context.user_data['first_name'] = first_name
        else:
            context.user_data['patronymic'] = update.message.text
    
    phone_request_button = KeyboardButton('Передать контакт', request_contact=True)
    update.message.reply_text(
        'Введите номер телефона или передайте контакт',
        reply_markup=ReplyKeyboardMarkup(
            [[phone_request_button]],
            resize_keyboard=True,
            input_field_placeholder='8-999-999-9999',
        ),
    )
    return GET_PHONE


def correct_phone(update, context):
    if update.message.contact:
        phone_number = update.message.contact.phone_number
    else:
        phone_number = update.message.text
    context.user_data['phone'] = phone_number
    update.message.reply_text(
        'Введите серию и номер паспорта в формате "1234 567890"',
        reply_markup=ReplyKeyboardRemove(),
    )
    return GET_PASSPORT


def incorrect_phone(update, _):
    update.message.reply_text(
        'Пожалуйста, введите номер в формате: "8" и 10 цифр'
    )
    return GET_PHONE


def birthdate(update, context):
    context.user_data['passport'] = update.message.text
    update.message.reply_text(
        'Введите дату рождения в формате "ДД.ММ.ГГГГ"',
        reply_markup=ReplyKeyboardRemove(),
    )
    return GET_BIRTHDATE


def correct_birthdate(update, context):
    check_birthdate = check_age(update.message.text.replace(',','.'))
    if not check_birthdate:
        context.user_data['birthdate'] = update.message.text.replace(',','.')
    
        if not get_user(update.message.from_user.id):
            add_user(context.user_data)
    
        total_price = count_price(update, context)
        context.user_data['cost'] = total_price
    
        update.message.reply_text(
            f'Стоимость бронирования: {total_price} руб.',
            reply_markup=ReplyKeyboardMarkup(
                [['Оплатить']],
                resize_keyboard=True,
            ),
        )
        return TAKE_PAYMENT
    else:
        update.message.reply_text(check_birthdate)
        return ConversationHandler.END


def incorrect_birthdate(update, _):
    update.message.reply_text(
        'Пожалуйста, введите дату рождения в формате "8.12.1997"'
    )
    return GET_BIRTHDATE


def success_payment(update, context):
    reply_keyboard = [['Забронировать место', 'Вещи на хранении']]
    key,start,end = add_reservation(context.user_data)
    update.message.reply_text(
        'Оплата принята. Спасибо за бронирование!\n'
        'Вот ваш электронный ключ для доступа к вашему личному складу.\n'
        f'Вы сможете попасть на склад в любое время в период с {start} по {end}',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True),
    )
    code_path = get_code(key)
    with open(code_path, 'rb') as code:
        update.message.reply_photo(code)
    
    return GET_USER_CHOICE


def show_things(update, context):
    context.user_data['things'] = get_reservations(context.user_data['user_id'])
    if len(context.user_data['things']) > 1:
        reply_keyboard = [['Показать другую ячейку'], ['Забронировать место']]
    else:
        reply_keyboard = [['Забронировать место']]

    if context.user_data['things']:
        thing = context.user_data['things'].pop()
        update.message.reply_text(
                thing[0] + '\nQR-код:',
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard,
                    resize_keyboard=True,
                ),
            )
        code_path = get_code(thing[1])
        with open(code_path, 'rb') as code:
            update.message.reply_photo(code)
        
        return GET_SHOW_THINGS_CHOICE
    else:
        update.message.reply_text('У вас нет вещей на хранении')


def show_next_thing(update, context):
    if len(context.user_data['things']) > 1:
        reply_keyboard = [['Показать другую ячейку'], ['Забронировать место']]
    else:
        reply_keyboard = [['Забронировать место']]
    
    thing = context.user_data['things'].pop()
    update.message.reply_text(
            thing[0] + '\nQR-код:',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                resize_keyboard=True,
            ),
        )
    code_path = get_code(thing[1])
    with open(code_path, 'rb') as code:
        update.message.reply_photo(code)
    
    return GET_SHOW_THINGS_CHOICE


def get_things_confirmation_back(update, context):
    if context.user_data['supertype'] == 'Сезонные вещи':
        return get_seasoned_things_time_type(update, context)
    else:
        return get_other_things_area(update, context)


def get_personal_data_back(update, context):
    if context.user_data['supertype'] == 'Сезонные вещи':
        return get_seasoned_things_time(update, context)
    elif context.user_data['supertype'] == 'Другое':
        return get_other_things_time(update, context)
    else:
        return entity_order(update, context)


def get_things_type_back(update, context):
    if context.user_data['is_located']:
        return get_address_with_location(update, context)
    else:
        return get_address(update, context)


def incorrect_input(update, context):
    update.message.reply_text(
        'Я вас не понимаю \U0001F61F\n\n'
        'Пожалуйста, воспользуйтесь кнопками в нижнем меню.\n'
        'Если они у вас не отображаются, просто нажмите на эту\n'
        'кнопку в поле ввода:'
    )
    with open('pointer.jpeg', 'rb') as pointer_file:
        update.message.reply_photo(pointer_file)


def incorrect_fio(update, context):
    update.message.reply_text(
        'Я вас не понимаю \U0001F61F\n\n'
        'Пожалуйста, введите имя в формате Фамилия Имя'
        'или Фамилия Имя Отчество'
    )


if __name__ == '__main__':
    env = Env()
    env.read_env()
    BOT_TOKEN = env('BOT_TOKEN')
    updater = Updater(token=BOT_TOKEN)
    dispatcher = updater.dispatcher
    if not Path(selfstorage).is_file():
        create_db()
        add_prices()
        add_warehouses()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(Filters.regex('^Начать$'), start)],
        states={
            GET_ADDRESS_TYPE: [
                MessageHandler(Filters.regex('^Да, подскажите$'), get_user_location),
                MessageHandler(Filters.regex('^Нет, выберу сам$'), get_address),
                MessageHandler(Filters.text, incorrect_input),
            ],
            GET_USER_LOCATION: [
                MessageHandler(Filters.regex('^Назад ⬅$'), start),
                MessageHandler(Filters.text, get_address_with_location),
                MessageHandler(Filters.location, get_address_with_location)
            ],
            GET_ADDRESS: [
                MessageHandler(Filters.regex('^Назад ⬅$'), start),
                MessageHandler(Filters.text, get_things_type)
            ],
            GET_ADDRESS_WITH_LOCATION: [
                MessageHandler(Filters.regex('^Назад ⬅$'), get_user_location),
                MessageHandler(Filters.text, get_things_type)
            ],
            GET_THINGS_TYPE: [
                MessageHandler(Filters.regex('^Другое$'), get_other_things_area),
                MessageHandler(Filters.regex('^Сезонные вещи$'), get_seasoned_things_type),
                MessageHandler(Filters.regex('^Услуги для юридических лиц$'), entity_greetings),
                MessageHandler(Filters.regex('^Назад ⬅$'), get_things_type_back),
                MessageHandler(Filters.text, incorrect_input),
            ],
            # ветка других вещей
            GET_OTHER_THINGS_AREA: [
                MessageHandler(
                    Filters.regex(r'^\d{1,2} м² за \d{3,4} руб./мес.$'), get_other_things_time
                ),
                MessageHandler(Filters.regex('^Назад ⬅$'), get_things_type),
                MessageHandler(Filters.text, incorrect_input),
            ],
            # ветка сезонных вещей
            GET_SEASONED_THINGS_TYPE: [
                MessageHandler(Filters.regex('^Назад ⬅$'), get_things_type),
                MessageHandler(Filters.text, get_seasoned_things_count)
            ],
            GET_SEASONED_THINGS_COUNT: [
                MessageHandler(Filters.regex(r'^\d+$'), get_seasoned_things_time_type),
                MessageHandler(Filters.regex('^Назад ⬅$'), get_seasoned_things_type),
                MessageHandler(Filters.text, incorrect_input),
            ],
            GET_SEASONED_THINGS_TIME_TYPE: [
                MessageHandler(Filters.regex(r'Месяцы'), get_seasoned_things_time),
                MessageHandler(Filters.regex(r'Недели'), get_seasoned_things_time),
                MessageHandler(Filters.regex('^Назад ⬅$'), get_seasoned_things_count),
                MessageHandler(Filters.text, incorrect_input),
            ],
            # ветка услуг для юр. лиц
            GET_ENTITY_COUNT: [
                MessageHandler(Filters.regex('^Назад ⬅$'), get_things_type),
                MessageHandler(Filters.text('^Аренда стеллажей для хранения документов (899 руб./мес.)$'), entity_count),
                MessageHandler(Filters.text, incorrect_input),
            ],
            GET_ENTITY_ORDER: [
                MessageHandler(Filters.regex('^Назад ⬅$'), entity_order_back),
                MessageHandler(Filters.regex(r'^\d{1,2}$'), entity_order),
                MessageHandler(Filters.text, incorrect_input),
            ],
            ENTITY_ORDER_CONFIRMATION: [
                MessageHandler(Filters.text('Назад ⬅'), entity_order_confirmation_back),
                MessageHandler(Filters.regex(r'^\d{1,2} мес\.\n\(\d{2,6} руб\.\)$'), entity_order_confirmation),
                MessageHandler(Filters.text, incorrect_input),
            ],
            GET_THINGS_CONFIRMATION: [
                MessageHandler(Filters.regex(r'^\d{1,2} мес.$'), get_things_confirmation),
                MessageHandler(Filters.regex(r'^\d недел(я|и)$'), get_things_confirmation),
                MessageHandler(Filters.regex(r'^\d нед\.\n\(\d{2,5} руб\.\)$'), get_things_confirmation),
                MessageHandler(Filters.regex(r'^\d мес\.\n\(\d{2,6} руб\.\)$'), get_things_confirmation),
                MessageHandler(Filters.regex('^Назад ⬅$'), get_things_confirmation_back),
                MessageHandler(Filters.text, incorrect_input),
            ],
            GET_ACCEPT: [
                MessageHandler(Filters.regex('^Принимаю$'), name_from_contact),
                MessageHandler(Filters.regex('^Отказываюсь$'), accept_failure),
                MessageHandler(Filters.text, incorrect_input),
            ],
            GET_PERSONAL_DATA: [
                MessageHandler(Filters.regex('^Подтвердить$'), get_promocode),
                MessageHandler(Filters.regex('^Назад ⬅$'), get_personal_data_back),
                MessageHandler(Filters.text, incorrect_input),
            ],
            GET_NAME_INPUT_CHOICE: [
                MessageHandler(Filters.regex('^Добавить отчество$'), patronymic),
                MessageHandler(Filters.regex('^Ввести ФИО$'), full_name),
                MessageHandler(Filters.regex('^Пропустить$'), phone),
                MessageHandler(Filters.text, incorrect_input),
            ],
            GET_PATRONYMIC: [
                MessageHandler(Filters.regex('^[а-яА-Я]{6,20}$'), phone),
                MessageHandler(Filters.text, incorrect_input),
            ],
            GET_FULL_NAME: [
                MessageHandler(
                    Filters.regex(r'[а-яА-Я]{2,20}( )[а-яА-Я]{2,20}( )[а-яА-Я]{6,20}'),
                    phone
                ),
                MessageHandler(
                    Filters.regex(r'[а-яА-Я]{2,20}( )[а-яА-Я]{2,20}'),
                    phone
                ),
                MessageHandler(Filters.text, incorrect_fio),
            ],
            GET_PHONE: [
                MessageHandler(Filters.contact, correct_phone),
                MessageHandler(
                    Filters.regex(r'^\+?\d{1,3}?( |-)?\d{3}( |-)?\d{3}( |-)?\d{2}( |-)?\d{2}$'),
                    correct_phone,
                ),
                MessageHandler(Filters.text, incorrect_phone),
            ],
            GET_PASSPORT: [
                MessageHandler(Filters.regex(r'^\d{4}( )?\d{6}$'), birthdate),
                MessageHandler(Filters.text, incorrect_input),
            ],
            GET_BIRTHDATE: [
                MessageHandler(
                    Filters.regex(r'^(0?[1-9]|[12][0-9]|3[01])(.|,)(0?[1-9]|1[0-2])(.|,)(19|20)\d{2}$'),
                    correct_birthdate,
                ),
                MessageHandler(Filters.text, incorrect_birthdate),
            ],
            TAKE_PAYMENT: [
                MessageHandler(Filters.regex('^Оплатить$'), take_payment),
                MessageHandler(Filters.text, incorrect_input),
            ],
            PRECHECKOUT: [
                PreCheckoutQueryHandler(precheckout),
            ],
            SUCCESS_PAYMENT: [
                MessageHandler(Filters.successful_payment, success_payment)
            ],
            GET_USER_CHOICE: [
                MessageHandler(Filters.regex('^Вещи на хранении$'), show_things),
                MessageHandler(Filters.regex('^Забронировать место$'), get_address_type),
                MessageHandler(Filters.text, incorrect_input),
            ],
            GET_SHOW_THINGS_CHOICE: [
                MessageHandler(Filters.regex('^Забронировать место$'), get_address_type),
                MessageHandler(Filters.regex('^Показать другую ячейку$'), show_next_thing),
                MessageHandler(Filters.text, incorrect_input),
            ],
            GET_PROMOCODE: [
                MessageHandler(Filters.text, get_agreement_accept),
            ],
        },
        fallbacks=[CommandHandler('start', start), MessageHandler(Filters.regex('^Начать$'), start)],
        per_user=True,
        per_chat=False
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()
