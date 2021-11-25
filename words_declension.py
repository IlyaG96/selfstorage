
def num_with_week(num):
    if num == 1:
        return f'{num} неделя'
    elif 1 < num < 5:
        return f'{num} недели'
    elif num >= 5:
        return f'{num} недель'


def num_with_month(num):
    if num == 1:
        return f'{num} месяц'
    elif 1 < num < 5:
        return f'{num} месяца'
    elif num >= 5:
        return f'{num} месяцев'


def num_with_ruble(num):
    end_num = int(str(num)[-1])
    if num == 0:
        return f'{num} рублей'
    if num == 1:
        return f'{num} рубль'
    if 1 < num < 5:
        return f'{num} рубля'
    if 4 < num < 20:
        return f'{num} рублей'
    else:
        if end_num == 0:
            return f'{num} рублей'
        if end_num == 1:
            return f'{num} рубль'
        if 1 < end_num < 5:
            return f'{num} рубля'
        if 4 < num < 10:
            return f'{num} рублей'
