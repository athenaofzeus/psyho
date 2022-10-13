import form, re, telebot, requests, flask
from form import TOKEN, PROXY, secr_key, WEBHOOK_HOST, WEBHOOK_PORT
from datetime import datetime
from time import strftime
from telebot import types
from pymorphy2 import MorphAnalyzer

morph = MorphAnalyzer()
WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(TOKEN)
bot = telebot.TeleBot(TOKEN, threaded=False)
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH)

app = flask.Flask(__name__)

urls = ['-166858053', '-190422401']
us_word = ""
nums = []
current_year = ''
user_data = ''
posts_word = []

# keyboard /help
keyboard_1 = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
button_1 = types.KeyboardButton("/This_month")
button_2 = types.KeyboardButton("/This_year")
button_3 = types.KeyboardButton("/More_words")
keyboard_1.add(button_1, button_2, button_3)


def stat_month(mess_is_month, list_of_nums):
    same_month = 0
    for y in nums:
        # print(res_dat[y])
        if res_dat[y] == user_data:
            same_month += 1
    return same_month


def stat_year(mess_is_year, list_of_nums):
    same_year = 0
    for y in nums:
        if res_dat[y] != user_data and current_year in res_dat[y]:
            same_year += 1
    return same_year


# description for bot
@bot.message_handler(commands=["start", "help"])
def hi_func(message):
    # отправляем сообщение пользователю
    bot.send_message(message.chat.id,
                     "Вас приветствует бот-психолог."
                     "\n\n"
                     "Я ищу посты из пабликов ВК по психологии ('YouTalk' 'обними себя') с введенным вами словом. "
                     "Отправляю вам максимум 3 поста, а также могу дать статистку частоты использования данного слова за последний месяц и/или год. "
                     "Вам нужно только ввести лемму.")


def take_posts():
    data_1 = requests.get(
        "https://api.vk.com/method/wall.get",
        params={
            "owner_id": urls[0],
            'count': 100,
            "v": 5.84,  # версия API
            "access_token": secr_key,  # токен доступа
            "offset": 0
        }
    ).json()
    data_2 = requests.get(
        "https://api.vk.com/method/wall.get",
        params={
            "owner_id": urls[1],
            'count': 100,
            "v": 5.84,  # версия API
            "access_token": secr_key,  # токен доступа
            "offset": 0
        }
    ).json()
    dats_1 = []
    dats_2 = []
    text_1 = []
    text_2 = []
    for arr in data_1['response']['items']:
        full_1 = re.findall(r'\b\w+\b \d{2}, \d{4}',
                            datetime.fromtimestamp(arr["date"]).strftime("%A, %B %d, %Y %I:%M:%S"))
        for elem in full_1:
            prf_dat = re.sub(r'\d{2},', '', elem)
            dats_1.append(prf_dat)
        text_1.append(arr['text'])

    for arr in data_2['response']['items']:
        full_2 = re.findall(r'\b\w+\b \d{2}, \d{4}',
                            datetime.fromtimestamp(arr["date"]).strftime("%A, %B %d, %Y %I:%M:%S"))
        for elem in full_2:
            prfr_dat = re.sub(r'\d{2},', '', elem)
            dats_2.append(prfr_dat)
        text_2.append(arr['text'])

    com_text = [val for pair in zip(text_1, text_2) for val in pair]
    dats = [val for pair in zip(dats_1, dats_2) for val in pair]
    return com_text, dats


res_text, res_dat = take_posts()


def arr_post(res_text):
    clean_data = []
    for elem in res_text:
        puncts_spase = '\n|\t|\r'
        puncts_noth = ',|( — )|"|\(|\)|:|;|\.|!|\?'
        no_more_punct = re.sub(puncts_noth, '', elem)
        str_1 = re.sub(puncts_spase, ' ', no_more_punct)
        str_2 = re.sub(puncts_spase, ' ', str_1)
        less_spases = re.sub(r'( ){2,}', ' ', str_2)
        clean_data.append(less_spases)
    # print(clean_data)
    return clean_data


cleaned = arr_post(res_text)
# print(cleaned)


def lemma(cleaned):
    arr_words = []
    for el in cleaned:
        lems_arr = []
        words = el.split()
        for word in words:
            verb = morph.parse(word)
            # print(verb[0].normal_form)
            lems_arr.append(verb[0].normal_form)
        arr_words.append(lems_arr)
    # print(arr_words)
    return arr_words


lem = lemma(cleaned)


@bot.message_handler(regexp=r'[а-я]+')
def take_word(message):
    global us_word
    us_word = message.text.lower()
    global nums
    global posts_word
    nums.clear()
    posts_word.clear()
    for i in range(len(lem)):
        if us_word in lem[i]:
            # print(arr)
            num = i
            nums.append(num)
    # print(nums)
    for y in nums[:3]:
        if res_text[y] not in posts_word:
            posts_word.append(res_text[y])

    if len(nums) == 0:
        bot.send_message(message.chat.id, f"Вы ввели слово  '{us_word}'. К сожалению, слово не найдено, но вы можете ввести другое")
        bot.register_next_step_handler(message, take_word)
    else:
        bot.send_message(message.chat.id, f"Отлично, вы ввели слово  '{us_word}'. Вот найденные посты:")
        for el in posts_word:
            bot.send_message(message.chat.id, f"{el}")
        bot.send_message(message.chat.id, f"Хотите статистику или еще постов?", reply_markup=keyboard_1)



@bot.message_handler(commands=['This_month', 'This_year', 'More_words'])
def time_knowing(message):
    global current_year
    global user_data
    current_month = strftime('%B')
    current_year = strftime('%Y')
    user_data = f'{current_month}  {current_year}'
    if message.text == "/This_month":
        same_month = stat_month(message.text, nums)
        bot.send_message(message.chat.id, f"Вот сколько раз слово '{us_word}' было использовано в этом месяце:{same_month}")
        bot.send_message(message.chat.id, f"Хотите статистику или еще постов?", reply_markup=keyboard_1)

    elif message.text == "/This_year":
        same_year = stat_year(message.text, nums)
        bot.send_message(message.chat.id, f"Вот сколько раз слово '{us_word}' было использовано в этом году: {same_year}")
        bot.send_message(message.chat.id, f"Хотите статистику или еще постов?", reply_markup=keyboard_1)
    elif message.text == '/More_words':
        nums.clear()
        posts_word.clear()
        bot.send_message(message.chat.id, f"Хорошо, жду следующего слова")
        bot.register_next_step_handler(message, take_word)


# if __name__ == '__main__':
#     bot.polling(none_stop=True)


# пустая главная страничка для проверки
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'ok'


# обрабатываем вызовы вебхука = функция, которая запускается, когда к нам постучался телеграм
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)
