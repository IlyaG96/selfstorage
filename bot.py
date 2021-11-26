import logging
import re
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from environs import Env
from words_declension import num_with_week, num_with_month, num_with_ruble
from helpers import add_user, get_user, get_code


GET_ADDRESS, GET_ACCEPT, GET_THINGS_TYPE, GET_OTHER_THINGS_AREA, GET_THINGS_CONFIRMATION, GET_PERSONAL_DATA = range(6)
GET_SEASONED_THINGS_TYPE, GET_SEASONED_THINGS_COUNT = range(6, 8)
GET_NAME_INPUT_CHOICE, GET_PATRONYMIC, GET_FULL_NAME = range(8,11)
GET_PHONE, GET_PASSPORT, GET_BIRTHDATE, GET_PAYMENT_ACCEPT, GET_USER_CHOICE = range(11,16)


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


def get_things_type(update, context):
    context.user_data['warehouse_id'] = update.message.text[-1]

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


def get_other_things_area(update, context):
    context.user_data['supertype'] = update.message.text

    # replace with get from db
    start_price = 599
    add_price = 150

    things_areas_buttons = [
        [KeyboardButton(f'{area + 1} кв.м за {num_with_ruble(start_price + add_price * area)} в месяц')]
        for area in range(0, 10)
    ]

    reply_markup = ReplyKeyboardMarkup(things_areas_buttons)

    update.message.reply_text(
        'Выберите площадь необходимую для хранения ваших вещей',
        reply_markup=reply_markup
    )

    return GET_OTHER_THINGS_AREA


def get_other_things_time(update, context):
    area = re.match(r'^(\d{1,2}) кв\.м за \d{3,4} рубл(я|ей|ь) в месяц$', update.message.text).groups()[0]

    context.user_data['other_area'] = int(area)

    time_buttons = [
        [KeyboardButton(f'На {num_with_month(time)}')] for time in range(1, 13)
    ]

    reply_markup = ReplyKeyboardMarkup(time_buttons)

    update.message.reply_text(
        'Выберите на какой срок вы хотите снять ячейку хранения',
        reply_markup=reply_markup
    )

    return GET_THINGS_CONFIRMATION


def get_seasoned_things_type(update, context):
    context.user_data['supertype'] = update.message.text

    # Replace with get from db
    things_types = [
        'Лыжи', 'Сноуборд', 'Велосипед', 'Колеса'
    ]

    things_types_buttons = [
        [KeyboardButton(type_)] for type_ in things_types
    ]

    reply_markup = ReplyKeyboardMarkup(things_types_buttons)

    update.message.reply_text(
        'Выберите вещь, которую будете хранить',
        reply_markup=reply_markup
    )

    return GET_SEASONED_THINGS_TYPE


def get_seasoned_things_count(update, context):
    # Replace with get from db
    things_types = [
        'Лыжи', 'Сноуборд', 'Велосипед', 'Колеса'
    ]

    if update.message.text in things_types:
        context.user_data['seasoned_type'] = update.message.text
    else:
        return GET_SEASONED_THINGS_TYPE

    update.message.reply_text(
        'Напишите количество вещей',
        reply_markup=ReplyKeyboardRemove()
    )

    return GET_SEASONED_THINGS_COUNT


def get_seasoned_things_time(update, context):
    user_data = context.user_data
    user_data['seasoned_count'] = int(update.message.text)
    count = user_data['seasoned_count']

    # Replace with get from db
    things_price = {
        'Лыжи': (100, 300),
        'Сноуборд': (100, 300),
        'Колеса': (None, 50),
        'Велосипед': (150, 400)
    }
    thing = context.user_data['seasoned_type']
    result = f'Ваш заказ ({user_data["seasoned_count"]} {user_data["seasoned_type"]}) обойдется в '
    price = things_price.get(thing)
    week_price, month_price = price
    if week_price:
        result += f'{num_with_ruble(week_price * count)} в неделю или '
    result += f'{num_with_ruble(month_price * count)} в месяц'

    time_buttons = (
        ([[KeyboardButton(f'На {num_with_week(time)}')] for time in range(1, 4)] if week_price else [])
        + [[KeyboardButton(f'На {num_with_month(time)}')] for time in range(1, 7)]
    )

    reply_markup = ReplyKeyboardMarkup(time_buttons)

    update.message.reply_text(
        result
    )

    update.message.reply_text(
        'Выберите на какой срок вы хотите снять ячейку хранения',
        reply_markup=reply_markup
    )

    return GET_THINGS_CONFIRMATION


def get_things_confirmation(update, context):
    keyboard = [
        ['Подтвердить']
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard)

    user_data = context.user_data

    if user_data['supertype'] == 'Другое':
        time = re.match(r'^На (\d{1,2}) месяц(ев|а|)$', update.message.text).groups()[0]
        user_data['other_time'] = int(time)

        update.message.reply_text(
            f'Ваш заказ: \n'
            f'Тип: {user_data["supertype"]}\n'
            f'Площадь: {user_data["other_area"]}\n'
            f'Время хранения: {user_data["other_time"]}\n'
            f'Итоговая цена: N',
            reply_markup=reply_markup
        )
    elif user_data['supertype'] == 'Сезонные вещи':
        if 'месяц' in update.message.text:
            time = int(re.match(r'^На (\d{1,2}) месяц(ев|а|)$', update.message.text).groups()[0])
            time_type = 'month'
        elif 'недел' in update.message.text:
            time = int(re.match(r'^На (\d) недел(я|и)$', update.message.text).groups()[0])
            time_type = 'week'

        user_data['seasoned_time'] = time
        user_data['seasoned_time_type'] = time_type

        update.message.reply_text(
            f'Ваш заказ: \n'
            f'Тип: {user_data["seasoned_type"]}\n'
            f'Количество: {user_data["seasoned_count"]}\n'
            f'Время хранения: {num_with_week(time) if time_type == "week" else num_with_month(time)}\n'
            f'Итоговая цена: N',
            reply_markup=reply_markup
        )

    return GET_PERSONAL_DATA


def get_agreement_accept(update, _):
    keyboard = [
        [
            KeyboardButton('Принимаю'),
            KeyboardButton('Отказываюсь')
        ]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard)

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


def name_from_contact(update, _):
    user = update.message.from_user
    first_name = user.first_name
    last_name = user.last_name
    if first_name and last_name:
        reply_keyboard = [
            ['Добавить отчество', 'Ввести ФИО'],
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
    message_parts = update.message.text.split()
    if len(message_parts) == 3:
        last_name, first_name, patronymic = message_parts
        context.user_data['last_name'] = last_name
        context.user_data['first_name'] = first_name
        context.user_data['patronymic'] = patronymic
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
    context.user_data['birthdate'] = update.message.text

    if not get_user(update.message.from_user.id):
        add_user(context.user_data)

    update.message.reply_text(
        'Стоимость бронирования: N руб.',
        reply_markup=ReplyKeyboardMarkup([['Оплатить']],
        resize_keyboard=True,
        ),
    )
    return GET_PAYMENT_ACCEPT


def incorrect_birthdate(update, context):
    update.message.reply_text(
        'Пожалуйста, введите дату рождения в формате "8.12.1997"'
    )
    return GET_BIRTHDATE


def success_payment(update, context):
    update.message.reply_text(
        'Будем считать, что оплата прошла )\n'
        'Ваш код для доступа в хранилище:',
        reply_markup=ReplyKeyboardRemove(),
    )
    code_path = get_code(context.user_data)
    with open(code_path, 'rb') as code:
        update.message.reply_photo(code)


def tmp_reply(update, _):
    update.message.reply_text(
        'В разработке...',
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
                MessageHandler(Filters.regex('^Другое$'), get_other_things_area),
                MessageHandler(Filters.regex('^Сезонные вещи$'), get_seasoned_things_type)
            ],
            # ветка других вещей
            GET_OTHER_THINGS_AREA: [
                MessageHandler(Filters.regex(r'^\d{1,2} кв\.м за \d{3,4} рубл(я|ей|ь) в месяц$'), get_other_things_time)
            ],
            # ветка сезонных вещей
            GET_SEASONED_THINGS_TYPE: [
                MessageHandler(Filters.text, get_seasoned_things_count)
            ],
            GET_SEASONED_THINGS_COUNT: [
                MessageHandler(Filters.regex(r'^\d+$'), get_seasoned_things_time)
            ],
            GET_THINGS_CONFIRMATION: [
                MessageHandler(Filters.regex(r'^На \d{1,2} месяц(ев|а|)$'), get_things_confirmation),
                MessageHandler(Filters.regex(r'^На \d недел(я|и)$'), get_things_confirmation)
            ],
            GET_ACCEPT: [
                MessageHandler(Filters.regex('^Принимаю$'), name_from_contact),
                MessageHandler(Filters.regex('^Отказываюсь$'), accept_failure),
            ],
            GET_PERSONAL_DATA: [
                MessageHandler(Filters.regex('^Подтвердить$'), get_agreement_accept),
            ],
            GET_NAME_INPUT_CHOICE: [
                MessageHandler(Filters.regex('^Добавить отчество$'), patronymic),
                MessageHandler(Filters.regex('^Ввести ФИО$'), full_name),
            ],
            GET_PATRONYMIC: [
                MessageHandler(Filters.regex('^[а-яА-Я]{6,20}$'), phone),
            ],
            GET_FULL_NAME: [
                MessageHandler(
                    Filters.regex('[а-яА-Я]{2,20}( )[а-яА-Я]{2,20}( )[а-яА-Я]{6,20}'),
                    phone
                ),
            ],
            GET_PHONE: [
                MessageHandler(Filters.contact, correct_phone),
                MessageHandler(
                    Filters.regex('^\+?\d{1,3}?( |-)?\d{3}( |-)?\d{3}( |-)?\d{2}( |-)?\d{2}$'),
                    correct_phone,
                ),
                MessageHandler(Filters.text, incorrect_phone),
            ],
            GET_PASSPORT: [
                MessageHandler(Filters.regex('^\d{4}( )?\d{6}$'), birthdate),
            ],
            GET_BIRTHDATE: [
                MessageHandler(
                    Filters.regex('^(0?[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.19|20\d{2}$'),
                    correct_birthdate,
                ),
                MessageHandler(Filters.text, incorrect_birthdate),
            ],
            GET_PAYMENT_ACCEPT: [
                MessageHandler(Filters.regex('^Оплатить$'), success_payment),
            ],
            GET_USER_CHOICE: [
                MessageHandler(Filters.regex('^Забронировать место|Вещи на хранении$'), tmp_reply),
            ],
        },
        fallbacks=[CommandHandler('start', start), MessageHandler(Filters.regex('^Начать$'), start)],
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()
