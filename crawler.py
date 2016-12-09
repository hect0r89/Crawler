import threading

from lxml import html
import json
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from time import sleep
from pip._vendor import requests
import telebot

TOKEN = '315180191:AAEG7IUuRyAE6WQ8gOAKIBHDu4w8jxAbfiY'  # Ponemos nuestro TOKEN generado con el @BotFather
READING = False
AsinList = []
suscribers = []
bot = telebot.TeleBot(TOKEN)


def AmzonParser(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}
    page = requests.get(url, headers=headers)
    while True:
        sleep(3)
        try:
            doc = html.fromstring(page.content)
            XPATH_NAME = '//h1[@id="title"]//text()'
            XPATH_SALE_PRICE = '//span[contains(@id,"ourprice") or contains(@id,"saleprice")]/text()'
            XPATH_ORIGINAL_PRICE = '//span[contains(@class,"a-text-strike")]/text()'
            XPATH_CATEGORY = '//a[@class="a-link-normal a-color-tertiary"]//text()'
            XPATH_AVAILABILITY = '//div[@id="availability"]//text()'

            RAW_NAME = doc.xpath(XPATH_NAME)
            RAW_SALE_PRICE = doc.xpath(XPATH_SALE_PRICE)
            RAW_CATEGORY = doc.xpath(XPATH_CATEGORY)
            RAW_ORIGINAL_PRICE = doc.xpath(XPATH_ORIGINAL_PRICE)
            RAw_AVAILABILITY = doc.xpath(XPATH_AVAILABILITY)

            NAME = ' '.join(''.join(RAW_NAME).split()) if RAW_NAME else None
            SALE_PRICE = ' '.join(''.join(RAW_SALE_PRICE).split()).strip() if RAW_SALE_PRICE else None
            CATEGORY = ' > '.join([i.strip() for i in RAW_CATEGORY]) if RAW_CATEGORY else None
            ORIGINAL_PRICE = ''.join(RAW_ORIGINAL_PRICE).strip() if RAW_ORIGINAL_PRICE else None
            AVAILABILITY = ''.join(RAw_AVAILABILITY).strip() if RAw_AVAILABILITY else None

            if not ORIGINAL_PRICE:
                ORIGINAL_PRICE = SALE_PRICE

            if page.status_code != 200:
                raise ValueError('captha')
            data = {
                'NAME': NAME,
                'SALE_PRICE': SALE_PRICE,
                'CATEGORY': CATEGORY,
                'ORIGINAL_PRICE': ORIGINAL_PRICE,
                'AVAILABILITY': AVAILABILITY,
                'URL': url,
            }

            return data
        except Exception as e:
            print(e)


# def sendEmail(product_name, original_price, actual_price, url):
#     server = smtplib.SMTP('smtp.mail.yahoo.com', 587)
#     server.starttls()
#     server.set_debuglevel(1)
#     server.login("notificacioncrawler@yahoo.com", "C0ntrPrYh00")
#
#     msg = MIMEText(
#         'El precio del producto {0} ha cambiado.\n Antes costaba {1} y ahora cuesta {2}. \n Puedes consultarlo en {3}'.format(
#             product_name, original_price, actual_price, url), 'plain', 'utf-8')
#     msg['Subject'] = Header('Cambios en precios de Amazon', 'utf-8')
#     msg['From'] = "notificacionCrawler@yahoo.com"
#     msg['To'] = "hectordediego89@gmail.com"
#     server.sendmail("notificacioncrawler@yahoo.com", "migueldediegoamo@hotmail.com", msg.as_string())
#     server.quit()


def ReadAsin():
    global READING

    # server = smtplib.SMTP('smtp.mail.yahoo.com', 587)
    # server.starttls()
    # server.set_debuglevel(1)
    # server.login("notificacioncrawler@yahoo.com", "C0ntrPrYh00")
    # AsinList = csv.DictReader(open(os.path.join(os.path.dirname(__file__),"Asinfeed.csv")))

    changes = False
    file_created = False
    extracted_data = {}
    try:
        with open('data.json') as data_file:
            data_json = json.load(data_file)
            file_created = True
    except Exception as e:
        data_json = {}
        print(e)
    READING = True
    for i in AsinList:
        url = i
        print("Processing: " + url)
        data = AmzonParser(url)
        if data_json:
            if data_json.get(url):
                if data_json.get(url)['SALE_PRICE'] != data['SALE_PRICE'] and data['SALE_PRICE']:
                    print("Ha cambiado")
                    for suscriber in suscribers:
                        bot.send_message(suscriber,
                                         "El precio del producto {0} ha cambiado.\n Antes costaba {1} y ahora cuesta {2}. \n Puedes consultarlo en {3}".format(
                                             data['NAME'], data_json.get(url)['SALE_PRICE'], data['SALE_PRICE'],
                                             data['URL']))
                    # sendEmail(data['NAME'], data_json.get(url)['SALE_PRICE'], data['SALE_PRICE'], data['URL'])
                    changes = True
                else:
                    print("Igual")
            else:
                changes = True
        extracted_data[data['URL']] = data
        sleep(5)
    READING = False
    if (not file_created and AsinList) or changes:
        f = open('data.json', 'w')
        json.dump(extracted_data, f, indent=4)


def telegram_bot():
    @bot.message_handler(commands=['add'])
    def send_welcome(message):
        global AsinList
        if not READING:
            url = message.text[5:]
            if url.startswith('https://www.amazon.es'):
                if url not in AsinList:
                    AsinList.append(url)
                    f_urls = open('urls.json', 'w')
                    json.dump(AsinList, f_urls, indent=4)
                    bot.reply_to(message, "Producto añadido correctamente")
                else:
                    bot.reply_to(message, "Producto ya añadido")
            else:
                bot.reply_to(message, "URL no válida")
        else:
            bot.reply_to(message, "Servidor sobrecargado, espere unos segundos y vuelva a intentarlo")

    @bot.message_handler(commands=['delete'])
    def send_welcome(message):
        global AsinList
        if not READING:
            url = message.text[12:]
            if url.startswith('https://www.amazon.es'):
                if url in AsinList:
                    AsinList.remove(url)
                    f_urls = open('urls.json', 'w')
                    json.dump(AsinList, f_urls, indent=4)
                    bot.reply_to(message, "Producto eliminado correctamente")
                else:
                    bot.reply_to(message, "Producto no existente")
            else:
                bot.reply_to(message, "URL no válida")
        else:
            bot.reply_to(message, "Servidor sobrecargado, espere unos segundos y vuelva a intentarlo")

    @bot.message_handler(commands="start")
    def echo_all(message):
        bot.reply_to(message, "Bienvenido al canal de notificaciones de productos Amazon")

    @bot.message_handler(commands="suscribe")
    def echo_all(message):
        if not READING:
            global suscribers
            if message.chat.id not in suscribers:
                suscribers.append(message.chat.id)
                f_ids = open('ids.json', 'w')
                json.dump(suscribers, f_ids, indent=4)
                bot.reply_to(message, "Te has suscrito a las notificaciones")
            else:
                bot.reply_to(message, "Ya te encuentras suscrito al canal de notificaciones")
        else:
            bot.reply_to(message, "Servidor sobrecargado, espere unos segundos y vuelva a intentarlo")

    @bot.message_handler(commands="unsuscribe")
    def echo_all(message):
        if not READING:
            global suscribers
            if message.chat.id in suscribers:
                suscribers.remove(message.chat.id)
                f_ids = open('ids.json', 'w')
                json.dump(suscribers, f_ids, indent=4)
                bot.reply_to(message, "Te has dado de baja de las notificaciones")
        else:
            bot.reply_to(message, "Servidor sobrecargado, espere unos segundos y vuelva a intentarlo")

    @bot.message_handler(commands="products")
    def echo_all(message):
        try:
            with open('data.json') as data_file:
                data_json = json.load(data_file)
                str = ''
                for data in data_json:
                    str += '''Nombre: {0}
Precio: {1}
{2}

'''.format(data_json[data]['NAME'], data_json[data]['SALE_PRICE'], data_json[data]['URL'])
                bot.reply_to(message, str)
        except Exception as e:
            print(e)

    bot.polling()


if __name__ == "__main__":
    try:
        with open('urls.json') as urls_file:
            urls_json = json.load(urls_file)
            AsinList = urls_json
    except Exception as e:
        print(e)

    try:
        with open('ids.json') as ids_file:
            ids_json = json.load(ids_file)
            suscribers = ids_json
    except Exception as e:
        print(e)

    t = threading.Thread(target=telegram_bot)
    t.setDaemon(True)
    t.start()
    while True:
        ReadAsin()
        sleep(1800)
