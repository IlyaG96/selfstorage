from telegram import LabeledPrice
from environs import Env
from helpers import get_other_prices, get_seasoned_prices

TAKE_PAYMENT, PRECHECKOUT, SUCCESS_PAYMENT = range(20, 23)


def take_payment(update, context):

    price = count_price(update, context)

    env = Env()
    env.read_env()
    sb_token = env('SB_TOKEN')
    chat_id = update.message.chat_id
    title = "Тестовая оплата ячейки хранения"
    description = "Платим за ..."
    # select a payload just for you to recognize its the donation from your bot
    payload = "Custom-Payload"

    provider_token = sb_token
    currency = "RUB"
    # price in dollars
    # price * 100 so as to include 2 decimal points
    prices = [LabeledPrice("Test", price * 100)]

    # optionally pass need_name=True, need_phone_number=True,
    # need_email=True, need_shipping_address=True, is_flexible=True
    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )

    return PRECHECKOUT


def precheckout(update, _):
    query = update.pre_checkout_query
    # check the payload, is this from your bot?
    if query.invoice_payload != 'Custom-Payload':
        # answer False pre_checkout_query
        query.answer(ok=False, error_message="Что-то пошло не так...")
    else:
        query.answer(ok=True)

    return SUCCESS_PAYMENT

def count_price(update, context):

    user_data = context.user_data

    if user_data['supertype'] == 'Другое':
        prices = get_other_prices()
    else:
        prices = get_seasoned_prices()
        time = user_data['seasoned_time']
        time_type = user_data['seasoned_time_type']
        good = user_data["seasoned_type"]
        count = user_data["seasoned_count"]
        index = 1 if time_type == "month" else 0
        price = prices[good][index] * time * int(count)

        return price


