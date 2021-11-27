import random
import sqlite3
import string
from datetime import datetime, timedelta
from sqlite3 import Error

import qrcode


selfstorage = 'selfstorage.db'


def get_code(context_data):
    key = ''.join(random.choices(string.ascii_letters + string.digits, k = 32))
    img = qrcode.make(key)
    code_file = 'SelfStorage code.png'
    img.save(code_file)
    return code_file


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def create_db():
    sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                     id integer PRIMARY KEY,
                                     name text,
                                     patronymic text,
                                     surname text,
                                     phone text,
                                     passport text,
                                     birthdate integer,
                                     warehouse_id integer,
                                     access_start integer,
                                     access_end integer,
                                     key text,
                                     FOREIGN KEY (warehouse_id) REFERENCES warehouses (id)
                                 ); """

    sql_create_reservations_table = """CREATE TABLE IF NOT EXISTS reservations (
                                           id integer PRIMARY KEY,
                                           user_id integer,
                                           type text,
                                           count integer,
                                           reservation_start integer,
                                           reservation_end integer,
                                           cost integer,
                                           FOREIGN KEY (user_id) REFERENCES users (id)
                                       );"""

    sql_create_warehouses_table = """CREATE TABLE IF NOT EXISTS warehouses (
                                           id integer PRIMARY KEY,
                                           address text,
                                           short_name text,
                                           latitude real,
                                           longitude real
                                       );"""

    sql_create_prices_table = """CREATE TABLE IF NOT EXISTS prices (
                                           type text PRIMARY KEY,
                                           supertype text,
                                           cost_per_week integer,
                                           cost_per_month integer,
                                           sub_cost integer
                                       );"""

    sql_create_promos_table = """CREATE TABLE IF NOT EXISTS promos (
                                           code text PRIMARY KEY,
                                           promo_start integer,
                                           promo_end integer,
                                           discount integer
                                       );"""

    conn = create_connection(selfstorage)

    if conn is not None:
        create_table(conn, sql_create_warehouses_table)
        create_table(conn, sql_create_users_table)
        create_table(conn, sql_create_reservations_table)
        create_table(conn, sql_create_prices_table)
        create_table(conn, sql_create_promos_table)
    else:
        print("Error! Cannot create the database connection.")


def add_user(context_data):
    birthdate_str = context_data['birthdate']
    birthdate = datetime.strptime(f'{birthdate_str}', '%d.%m.%Y')
    user = (
        context_data['user_id'],
        context_data['first_name'],
        context_data['patronymic'],
        context_data['last_name'],
        context_data['phone'],
        context_data['passport'],
        birthdate,
        context_data['warehouse_id']
    )

    conn = create_connection(selfstorage)
    sql = ''' INSERT INTO users(id, name, patronymic, surname, \
                  phone, passport, birthdate, warehouse_id)
              VALUES(?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, user)
    conn.commit()


def add_reservation(context_data):
    conn = create_connection(selfstorage)
    cur = conn.cursor()
    cur.execute("SELECT id FROM reservations")
    reservation_ids = cur.fetchall()
    if reservation_ids:
        reservation_id = max(reservation_ids) + 1
    else:
        reservation_id = 1
    reservation_start = datetime.today()

    if context_data['supertype'] == 'Сезонные вещи':
        thing_type = context_data['seasoned_type']
        count = context_data['seasoned_count']
        if context_data['seasoned_time_type'] == 'week':
            period_in_weeks = context_data['seasoned_time']
        else:
            period_in_weeks = context_data['seasoned_time'] * 4
        reservation_end = reservation_start + timedelta(weeks=period_in_weeks)
    elif context_data['supertype'] == 'Другое':
        thing_type = 'Площадь'
        count = context_data['other_area']
        period_in_weeks = context_data['other_time'] * 4
        reservation_end = reservation_start + timedelta(weeks=period_in_weeks)

    cost = None

    reservation = (
        reservation_id,
        context_data['user_id'],
        thing_type,
        count,
        reservation_start,
        reservation_end,
        cost
    )

    conn = create_connection(selfstorage)
    sql = ''' INSERT INTO reservations(id, user_id, type, count, \
                  reservation_start, reservation_end, cost)
              VALUES(?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, reservation)
    conn.commit()


def get_reservations(user_id):
    conn = create_connection(selfstorage)
    cur = conn.cursor()
    cur.execute("SELECT type, count, reservation_end FROM reservations WHERE user_id=?", (user_id,))
    rows = cur.fetchall()
    reply = []
    for row in rows:
        if datetime.fromisoformat(row[2]) > datetime.today():
            time_dt = datetime.fromisoformat(row[2])
            time_out = time_dt.strftime("%d.%m.%Y")
            reply.append(f'Тип: {row[0]}, количество: {row[1]}\nПериод хранения: до {time_out}')
    return reply


def get_user(user_id):
    conn = create_connection(selfstorage)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    return cur.fetchone()


def add_prices():
    conn = create_connection(selfstorage)
    sql = ''' INSERT INTO prices(type, supertype, cost_per_week, cost_per_month, sub_cost)
              VALUES(?,?,?,?,?) '''
    cur = conn.cursor()

    cur.execute(sql, ('Лыжи', 'Сезонные вещи', 100, 300, None))
    cur.execute(sql, ('Сноуборд', 'Сезонные вещи', 100, 300, None))
    cur.execute(sql, ('Колеса', 'Сезонные вещи', None, 50, None))
    cur.execute(sql, ('Велосипед', 'Сезонные вещи', 150, 400, None))
    cur.execute(sql, ('Площадь', 'Другое', None, 599, 150))
    
    conn.commit()


def get_seasoned_things():
    conn = create_connection(selfstorage)
    cur = conn.cursor()
    cur.execute("SELECT type FROM prices WHERE supertype=?", ('Сезонные вещи',))
    rows = cur.fetchall()

    things = [row[0] for row in rows]

    return things


def get_seasoned_prices():
    conn = create_connection(selfstorage)
    cur = conn.cursor()
    cur.execute("SELECT type, cost_per_week, cost_per_month FROM prices WHERE supertype=?", ('Сезонные вещи',))
    rows = cur.fetchall()

    things_price = dict()
    for row in rows:
        things_price[row[0]] = (row[1], row[2])

    return things_price


def get_other_prices():
    conn = create_connection(selfstorage)
    cur = conn.cursor()
    cur.execute("SELECT cost_per_month, sub_cost FROM prices WHERE supertype=?", ('Другое',))
    row = cur.fetchone()
    
    price = (row[0], row[1])

    return price
