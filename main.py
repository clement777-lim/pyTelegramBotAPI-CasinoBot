import telebot
import sqlite3, random
from telebot import types
from telebot.types import ShippingOption, LabeledPrice

f = open('TOKENS.txt')
TOKENS = f.read().split('\n')

bot = telebot.TeleBot(TOKENS[0])  # Токен бота для работы с ним
paymant = TOKENS[1]

f.close()

keyboard_roullete = types.InlineKeyboardMarkup()  # Создание inline клавиатуры рулетки
buttons = [types.InlineKeyboardButton(text='0 🟢', callback_data='game_r_00')]  # Массив с кнопками

for i in range(1, 25):  # Всего 24 числа
    num = str(i)
    color = "⚫️" if i % 2 == 0 else "🟥"

    buttons.append(
        types.InlineKeyboardButton(text=num + color, callback_data=('game_r_' + (len(num) == 1) * '0' + num)))

for i in range(5):
    plus = 5 * i
    try:
        keyboard_roullete.row(buttons[1 + plus], buttons[2 + plus], buttons[3 + plus],
                              buttons[4 + plus], buttons[5 + plus])
    except IndexError:
        keyboard_roullete.row(buttons[1 + plus], buttons[2 + plus], buttons[3 + plus], buttons[4 + plus],
                              buttons[0])  # "0" идёт последним. Получается клавиатура 5 на 5

Black_butt = types.InlineKeyboardButton(text="⚫Чёрное⚫", callback_data='game_r_black')
Red_butt = types.InlineKeyboardButton(text="🟥Красное🟥", callback_data='game_r_red')

keyboard_roullete.add(Black_butt, Red_butt)  # Добавляем кнопки ставки на Черное или Красное


def main_keyboard():
    market = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    game_roullete = types.KeyboardButton(text='⚫️Рулетка🟥')
    ballance = types.KeyboardButton(text='💵Баланс💵')
    bonus_money = types.KeyboardButton(text='💸Бонус💸')

    market.add(game_roullete)
    market.add(ballance, bonus_money)

    return market


def SQL_request(request, one_or_all=True, ret_info=True):
    # If one_or_all=True - one, else all
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(request)

    if ret_info:
        if one_or_all:
            user_info = cursor.fetchone()[0]
        else:
            user_info = cursor.fetchall()

        return user_info

    else:
        conn.commit()


@bot.message_handler(commands=['start'])  # Реакция бота на комманду старт
def hello_message(message):

    id = message.from_user.id
    user_info = SQL_request(f"SELECT name FROM users WHERE id={id}")

    if not user_info:
        bot.send_message(message.chat.id, f"Ого, новый пользователь!\n Ну здравствуй, {message.from_user.first_name}",
                         reply_markup=main_keyboard())
        bot.send_message(message.chat.id,
                         f"Ты имеешь на счету стартовые 100 \n Для более подробного описания моего функционала "
                         f"напиши команду /help")

        new_user = (message.from_user.first_name, id, 100, 0, 0)

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO users
                          VALUES (?,?,?,?,?)""", new_user)
        conn.commit()

    else:
        bot.send_message(message.chat.id, f'Приветствую, {user_info}! \n\n Если нужна помощь - /help',
                         reply_markup=main_keyboard())
        # print(user_info[0], user_info[1], user_info[2], user_info[3], user_info[4])


@bot.message_handler(commands=['help'])  # Реакция бота на комманду help
def help_message(message):
    text = 'Привет, это бот, позволяющий испытать свою удачу. Для этого используются 💸.' \
           '\n      Начальный счёт - 100💸. Для того, чтобы узнать свой баланс, нажми специальную кнопку Баланс.' \
           '\n \n Для начала игры просто нажми на кнопку Рулетка или напиши в чат с помощью клавиатуры. ' \
           '\n      По умолчанию ставка ' \
           'равна 5💸. \n Для изменения ставки напиши в чат Рулетка [размер ставки]'
    bot.send_message(message.chat.id, text)


@bot.callback_query_handler(func=lambda call: True)  # Обработка запросов от моих клавиатур
def callback_inline(call):
    if 'game_r_' in call.data:

        win = False
        k = 2
        bet = int(call.message.text[30:])
        print(bet)

        random_bid = random.randint(0, 24)
        data = call.data[7:]
        color = "⚫️" if int(random_bid) % 2 == 0 else "🟥"
        color = "🟢" if random_bid == 0 else color

        id = call.from_user.id
        user_info = SQL_request(f"SELECT money FROM users WHERE id={id}")

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f'Твоя ставка - {data}')
        print(call)

        def win_or_lose(k=2, win=True):
            if win:
                bot.send_message(call.message.chat.id,
                                 f"Выпало число - {random_bid}{color}; {call.from_user.first_name} везунчик!"
                                 f"\n \n Твой выигрыш = {bet * k}💸. Баланс = {user_info + bet * k}💲")

            else:
                bot.send_message(call.message.chat.id,
                                 f"Выпало число - {random_bid}{color}; {call.from_user.first_name} лошок :("
                                 f"\n \nТы проиграл = {bet}💸. Баланс = {user_info - bet}💲")

        if len(data) == 2:
            users_bid = int(data)

            if random_bid == users_bid:
                if users_bid == 0:
                    k = 30

                else:
                    k = 25

                win_or_lose(k)
                win = True

            else:
                win_or_lose(win=False)

        elif data in ("black", "red"):
            parity = 0 if data == "black" else 1

            if random_bid != 0 and random_bid % 2 == parity:
                win = True
                win_or_lose()
            else:
                win_or_lose(win=False)

        if not win:
            SQL_request(f"UPDATE users SET money = {user_info - bet} WHERE id = {id}", ret_info=False)
        else:
            SQL_request(f"UPDATE users SET money = {user_info + bet * k} WHERE id = {id}", ret_info=False)


@bot.message_handler(content_types=['text'])
def game_roullete(message):
    id = message.from_user.id
    user_info = SQL_request(f"SELECT money FROM users WHERE id={id}")

    if '⚫️Рулетка🟥' == message.text[:10]:

        bet = 5

        if bet <= user_info:
            bot.send_message(message.chat.id, f"На что ставите? Ваша ставка = 5", reply_markup=keyboard_roullete)
        else:
            bot.send_message(message.chat.id, f"Оу, что-то денег маловато, сделай ставку поменьше. \n\n"
                                              f"     Баланс = 💲{user_info}💲")

    elif 'Рулетка' == message.text[:7]:

        if message.text[7:]:
            try:
                bet = abs(int(message.text[7:]))
            except ValueError:
                et = 5
        else:
            bet = 5

        if bet <= user_info:
            bot.send_message(message.chat.id, f"На что ставите? Ваша ставка = {bet}", reply_markup=keyboard_roullete)
        else:
            bot.send_message(message.chat.id, f"Оу, что-то денег маловато, сделай ставку поменьше. \n\n"
                                              f"     Баланс = 💲{user_info}💲")

    elif 'Баланс' in message.text:

        bot.send_message(message.chat.id, ("💲" + str(user_info) + "💲"))
    elif 'Купить' in message.text:

        if message.text[6:]:
            try:
                count = int(message.text[6:])
                if count < 1000 or count > 100000000:
                    raise SyntaxError

            except ValueError:
                bot.send_message(message.chat.id, 'Введи корректное количество 💸')

            except SyntaxError:
                bot.send_message(message.chat.id, 'Введите число >800💸 или <100000')

            else:
                price = [LabeledPrice(f'Денюжки💸', count)]

                bot.send_invoice(message.chat.id, title=f'Денюжки',
                                 provider_token=paymant, currency='RUB',
                                 is_flexible=False, prices=price,
                                 description=f'💸{count}💸', invoice_payload='Test')

    elif '💸Бонус💸' == message.text:
        id = message.from_user.id
        last_bonus_time = SQL_request(f'SELECT games FROM users WHERE id={id}')
        now = message.date

        delta = now - last_bonus_time

        if delta < 64800:
            delta = 64800 - delta
            bot.send_message(message.chat.id, f"Ты можешь каждый день получать бонус 50💸. \n"
                                              f"Осталось подождать:"
                                              f"\n {'  '* 20}{delta // 3600}ч {(delta // 60) % 60}м {delta % 60}с")
        else:
            user_info = SQL_request(f"SELECT money FROM users WHERE id={id}")
            SQL_request(f"UPDATE users SET money = {user_info + 50} WHERE id = {id}", ret_info=False)
            SQL_request(f"UPDATE users SET games = {now} WHERE id = {id}", ret_info=False)

            bot.send_message(message.chat.id, f"Вам начислено 50💸.Можешь забрать ещё через 18 часов"
                                              f"\n\n        Баланс = {user_info + 50}💸 \n")


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    bot.send_message(message.chat.id, 'Успешная покупка!')

    id = message.from_user.id
    user_info = SQL_request(f"SELECT money FROM users WHERE id={id}")

    total_amount = message.successful_payment.total_amount + user_info

    SQL_request(f"UPDATE users SET money = {total_amount} WHERE id = {id}", ret_info=False)
    # print(message.successful_payment.total_amount)


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Оплата не прошла - попробуйте, пожалуйста, еще раз,"
                                                "или свяжитесь с администратором бота.")


bot.infinity_polling()  # none_stop=True, interval=0, timeout=100)
