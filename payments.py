from telegram import LabeledPrice, ReplyKeyboardRemove
from environs import Env
from db_helpers import get_other_prices, get_seasoned_prices, get_entity_price
from words_declension import num_with_ruble

TAKE_PAYMENT, PRECHECKOUT, SUCCESS_PAYMENT = range(20, 23)


def take_payment(update, context):

    price = count_price(update, context)

    update.message.reply_text('Формирую счёт...', reply_markup=ReplyKeyboardRemove())

    env = Env()
    env.read_env()
    sb_token = env('SB_TOKEN')
    chat_id = update.message.chat_id
    title = "Ваш заказ"
    description = f"Оплата вашего заказа стоимостью {num_with_ruble(price)}"
    payload = "Custom-Payload"

    provider_token = sb_token
    currency = "RUB"
    prices = [LabeledPrice("Стоимость", price * 100)]

    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )

    return PRECHECKOUT


def precheckout(update, _):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Custom-Payload':
        query.answer(ok=False, error_message="Что-то пошло не так...")
    else:
        query.answer(ok=True)

    return SUCCESS_PAYMENT


def count_price(update, context):

    user_data = context.user_data

    if user_data['supertype'] == 'Другое':
        prices = get_other_prices()
        area = user_data["other_area"]
        time = user_data["other_time"]
        price = (prices[0] + area*prices[1])*time

        return price

    elif user_data['supertype'] == 'Сезонные вещи':
        prices = get_seasoned_prices()
        time = user_data['seasoned_time']
        time_type = user_data['seasoned_time_type']
        good = user_data["seasoned_type"]
        count = user_data["seasoned_count"]
        index = 1 if time_type == "month" else 0
        price = prices[good][index] * time * int(count)

        return price

    else:
        rack_price = get_entity_price()
        time = user_data['entity_time']
        count = user_data['entity_rack_count']
        price = rack_price*time*count

        return price