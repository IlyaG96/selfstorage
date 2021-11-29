import random
import sqlite3
import string
from datetime import datetime, timedelta
from sqlite3 import Error

import qrcode


selfstorage = 'selfstorage.db'


def get_code(key):
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
                                     birthdate integer
                                 ); """

    sql_create_reservations_table = """CREATE TABLE IF NOT EXISTS reservations (
                                           id integer PRIMARY KEY,
                                           user_id integer,
                                           warehouse_id integer,
                                           type text,
                                           count integer,
                                           reservation_start integer,
                                           reservation_end integer,
                                           cost integer,
                                           key text,
                                           FOREIGN KEY (user_id) REFERENCES users (id),
                                           FOREIGN KEY (warehouse_id) REFERENCES warehouses (id)
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
        birthdate
    )

    conn = create_connection(selfstorage)
    sql = ''' INSERT INTO users(id, name, patronymic, surname, \
                  phone, passport, birthdate)
              VALUES(?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, user)
    conn.commit()


def add_reservation(context_data):
    conn = create_connection(selfstorage)
    cur = conn.cursor()
    cur.execute("SELECT id FROM reservations ORDER BY id DESC LIMIT 1")
    reservation_max_id = cur.fetchone()
    if reservation_max_id:
        reservation_id = reservation_max_id[0] + 1
    else:
        reservation_id = 1
    reservation_start = datetime.today()
    start = reservation_start.strftime("%d.%m.%Y")

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

    else:
        thing_type = 'Стеллаж для хранения документов'
        count = context_data['entity_rack_count']
        period_in_weeks = context_data['entity_time'] * 4
        reservation_end = reservation_start + timedelta(weeks=period_in_weeks)

    end = reservation_end.strftime("%d.%m.%Y")    

    cost = context_data['cost']
    key = ''.join(random.choices(string.ascii_letters + string.digits, k = 32))

    reservation = (
        reservation_id,
        context_data['user_id'],
        context_data['warehouse_id'],
        thing_type,
        count,
        reservation_start,
        reservation_end,
        cost,
        key
    )

    conn = create_connection(selfstorage)
    sql = ''' INSERT INTO reservations(id, user_id, warehouse_id, type, count, \
                  reservation_start, reservation_end, cost, key)
              VALUES(?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, reservation)
    conn.commit()

    return (key, start, end)


def get_reservations(user_id):
    conn = create_connection(selfstorage)
    cur = conn.cursor()
    sql = ''' SELECT type, count, reservation_end, key, warehouses.short_name
              FROM reservations JOIN warehouses ON reservations.warehouse_id = warehouses.id
              WHERE user_id=? AND type <> ? '''
    cur.execute(sql, (user_id,'Площадь',))
    rows = cur.fetchall()
    reply = []
    for row in rows:
        if datetime.fromisoformat(row[2]) > datetime.today():
            time_dt = datetime.fromisoformat(row[2]) + timedelta(days=1)
            time_out = time_dt.strftime("%d.%m.%Y")
            reply.append((f'{row[0]}, {row[1]} шт.\nСклад {row[4]}\nПериод хранения: до {time_out}', row[3]))
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
    cur.execute(sql, ('Колеса', 'Сезонные вещи', 13, 50, None))
    cur.execute(sql, ('Велосипед', 'Сезонные вещи', 150, 400, None))
    cur.execute(sql, ('Площадь', 'Другое', None, 599, 150))
    cur.execute(sql, ('Аренда стеллажа', 'Услуги для юридических лиц', None, 899, None))
    
    conn.commit()


def add_warehouses():
    conn = create_connection(selfstorage)
    sql = ''' INSERT INTO warehouses(id, address, short_name, latitude, longitude)
              VALUES(?,?,?,?,?) '''
    cur = conn.cursor()

    warehouses = [
        [1, 'Рязанский пр., 16 строение 4', 'Рязань', 55.723217, 37.76623],
        [2, 'ул. Наташи Ковшовой, 2', 'Наташа', 55.683941000000004, 37.454796513441636],
        [3, 'Люблинская ул., 60 корпус 2', 'Люблино', 55.672881849999996, 37.737601749999996],
        [4, 'Походный пр-д, 6', 'Поход', 55.7520514, 37.5669518],
    ]

    for warehouse in warehouses:
        cur.execute(sql, warehouse)

    conn.commit()


def get_seasoned_things():
    conn = create_connection(selfstorage)
    cur = conn.cursor()
    cur.execute("SELECT type FROM prices WHERE supertype=?", ('Сезонные вещи',))
    rows = cur.fetchall()

    things = [row[0] for row in rows]

    return things


def get_warehouses_with_short_name():
    conn = create_connection(selfstorage)
    cur = conn.cursor()
    cur.execute("SELECT address, short_name FROM warehouses")
    rows = cur.fetchall()

    warehouses = dict()
    for row in rows:
        warehouses[row[0]] = row[1]

    return warehouses


def get_warehouse_coords_by_address(warehouse_address):
    conn = create_connection(selfstorage)
    cur = conn.cursor()
    cur.execute("SELECT latitude, longitude FROM warehouses WHERE address = ?", [warehouse_address])
    row = cur.fetchone()

    return row[0], row[1]


def get_warehouse_id_by_short_name(warehouse_short_name):
    conn = create_connection(selfstorage)
    cur = conn.cursor()
    cur.execute("SELECT id FROM warehouses WHERE short_name = ?", [warehouse_short_name])
    row = cur.fetchone()

    return row[0]


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


def get_entity_price():
    conn = create_connection(selfstorage)
    cur = conn.cursor()
    cur.execute("SELECT cost_per_month FROM prices WHERE supertype=?", ('Услуги для юридических лиц',))
    row = cur.fetchone()
    price = (row[0])

    return price

