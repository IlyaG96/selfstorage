from datetime import datetime, timedelta


def build_menu(buttons, n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def check_age(birthdate):
    birthdate_dt = datetime.strptime(f'{birthdate}', '%d.%m.%Y')
    age = (datetime.today() - birthdate_dt) // timedelta(days=365.2425)
    if age < 14:
        return 'Вы слишком молоды, чтобы бронировать у нас место'
    elif age > 100:
        return 'Вы уже не в том возрасте, чтобы бронировать у нас место'
    else:
        return ''
