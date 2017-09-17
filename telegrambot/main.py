import cyclos_api
import telepot
import logging
import asyncio

import sys
sys.path.append('../cyclosbot/')
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cyclosbot.settings")
import django
django.setup()
from telepot.aio.delegate import (pave_event_space, per_chat_id,
                                  create_open)
from config import (TOKEN, TIMEOUT, DEBUG_LEVEL, LOG_DIR, ADMINID)
from bot.models import TelegramUser
from django.core.exceptions import ObjectDoesNotExist
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton


class BotHandler(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(BotHandler, self).__init__(*args, **kwargs)
        self.advert_parent_category = None
        self.categories = [[]]
        self.subcategories = [[]]
        self.flow = {0: self.wait_username, 1: self.wait_password,
                     2: self.new_advert, 3: self.new_advert,
                     4: self.ask_advert_title, 5: self.ask_advert_body,
                     6: self.ask_price, 7: self.report_problem
                     }
        self.entry_point = {'saldo': self.account_balance,
                            'ayuda': self.send_help,
                            'nuevo anuncio': self.new_advert,
                            'reportar': self.report_problem, }
        self.default_keyboard = ReplyKeyboardMarkup(keyboard=[['Saldo', 'Nuevo anuncio', 'Ayuda'],
                                                              ['Reportar']])

    # This is called when a new message arrives
    async def on_chat_message(self, msg):
        content_type, chat_type, this_chat_id = telepot.glance(msg)

        logging.info("received message from: %s", this_chat_id)
        logging.debug(msg['text'])

        try:
            me = TelegramUser.objects.get(chat_id=this_chat_id)
        except ObjectDoesNotExist:
            me = None
        if me is not None:
            await self.process(msg, me)
        else:
            await self.register(msg, this_chat_id)

    # it will register the new user in the bd
    async def register(self, msg, this_chat_id):
        me = TelegramUser(chat_id=this_chat_id, conversation_flow=0)
        me.save()
        await self.sender.sendMessage('No estás registrado, vamos a'
                                      + ' solucionarlo, primero dime '
                                      + ' tu usuario de la web')

    #process the message
    async def process(self, msg, me):
        if msg['text'].lower() == '/cancel':
            await self.sender.sendMessage('Cancelando',
                                          reply_markup=self.default_keyboard)
            me.conversation_flow = 99
            me.save()
            logging.debug('Conversation flow = %s',me.conversation_flow)
        elif (me.conversation_flow < 8):
            await self.flow[me.conversation_flow](msg, me)
        else:
            await self.entry_point[msg['text'].lower()](msg, me)

    async def wait_username(self, msg, me):
        me.username = msg['text']
        me.conversation_flow = 1
        me.save()
        await self.sender.sendMessage('Muy bien, ahora dime tu '
                                      + 'contraseña (la misma que '
                                      + 'en la web')

    async def wait_password(self, msg, me):
        me.password = msg['text']
        me.save()
        await self.sender.sendMessage('Dame un momento para '
                                      + 'comprobar tus '
                                      + 'credenciales')
        if (await self.check_register(me.username, me.password)):
            # if works
            await self.sender.sendMessage('Enhorabuena, ya puedes '
                                          + 'acceder a cyclos a '
                                          + 'través de mi',
                                          reply_markup=self.default_keyboard)
            me.conversation_flow = 99
            me.save()
            await self.send_help(msg, me)
        else:
            # if don't works
            await self.sender.sendMessage('Vaya, parece que tus '
                                          + ' credenciales no son '
                                          + 'válidas')
            await self.sender.sendMessage('Por favor revísalas y '
                                          + 'lo intentamos otra vez')
            await self.sender.sendMessage('Empecemos por el nombre '
                                          + ' de usuario')
            me.conversation_flow = 0
            me.save()

    async def send_help(self, msg, me):
        await self.sender.sendMessage('Esta es la lista de  comandos')
        await self.sender.sendMessage('Saldo: devuelve el saldo actual')
        await self.sender.sendMessage('Nuevo anuncio: Crear un anuncio nuevo')
        await self.sender.sendMessage('Ayuda: muestra esta ayuda',
                                      reply_markup=self.default_keyboard)

    async def account_balance(self, msg, me):
        logging.debug("Waiting api answer")
        data = cyclos_api.get_account_balance(me.username, me.password)
        logging.debug("Received api answer")
        logging.info("Sending answer to: %s", me.chat_id)

        await self.sender.sendMessage('Saldo: ' + data['balance'] +
                                      '\nCrédito disponible: ' +
                                      data['availableBalance'],
                                      reply_markup=self.default_keyboard)

    async def new_advert(self, msg, me):
        data = cyclos_api.get_marketplace_info(me.username, me.password)

        # for each parent category, create new list, and append to
        # the main list, then create a keyboard using this list and
        # send it
        if me.conversation_flow is not 2 and me.conversation_flow is not 3:
            if len(data['categories']) > 0:
                for parent in data['categories']:
                    temps = []
                    temps.append(parent['name'])
                    self.categories.append(temps)

                markup = ReplyKeyboardMarkup(keyboard=self.categories,
                                             one_time_keyboard=True)
                await self.sender.sendMessage('Selecciona en que categoría '
                                              + 'deseas que aparezca el anuncio',
                                              reply_markup=markup)
                # set the flow to check the category in the next answer
                me.conversation_flow = 2
                me.save()
        elif me.conversation_flow is 2:
            # save the parent category
            self.advert_parent_category = msg['text']
            for parent in data['categories']:
                if parent['name'] == msg['text']:
                    for child in parent['children']:
                        temps = []
                        temps.append(child['name'])
                        self.subcategories.append(temps)

            markup = ReplyKeyboardMarkup(keyboard=self.subcategories,
                                         one_time_keyboard=True)
            await self.sender.sendMessage('Ahora elige la subcategoría'
                                          + ' que mejor encaje',
                                          reply_markup=markup)
            # set the flow to process the subcategory in the next answer
            me.conversation_flow = 3
            me.save()
        elif me.conversation_flow is 3:
            # set the flow to ask the title
            me.conversation_flow = 4
            me.save()
            # save the child category
            self.advert_child_category = msg['text']
            await self.sender.sendMessage('¿Cual será el título del anuncio?')

    async def ask_advert_title(self, msg, me):
        # set the flow to ask the body
        me.conversation_flow = 5
        me.save()
        self.advert_title = msg['text']
        await self.sender.sendMessage('¿Cual será el cuerpo del mensaje?')
        await self.sender.sendMessage('Recuerda hacerlo en un solo mensaje')

    async def ask_advert_body(self, msg, me):
        # set the flow to post the advert
        me.conversation_flow = 6
        me.save()
        self.advert_body = msg['text']
        await self.sender.sendMessage('¿Cuanto va a costar?')
        await self.sender.sendMessage('usa unidades enteras, los decimales'
                                      + ' no están soportados')
        # await self.sender.sendMessage('¿Que foto tendrá el anuncio?')

    async def ask_price(self, msg, me):
        if msg['text'].isdigit():
            self.advert_price = msg['text']
            await self.post_advert(msg, me)
        else:
            await self.sender.sendMessage('Por favor, introduce solo números'
                                          + ' en el precio, el uso de comas '
                                          + 'o puntos no está soportado')

    async def post_advert(self, msg, me):
        await self.sender.sendMessage('Voy a crear el anuncio, dame un momento')
        if cyclos_api.create_advert(me.username, me.password, self.advert_title, self.advert_body, self.advert_parent_category, self.advert_child_category, self.advert_price):
            await self.sender.sendMessage('El anuncio ha sido creado '
                                          + 'correctamente',
                                          reply_markup=self.default_keyboard)
        else:
            await self.sender.sendMessage('Ha ocurrido un error y el '
                                          + 'anuncio no ha podido ser '
                                          + 'creado',
                                          reply_markup=self.default_keyboard)
        me.conversation_flow = 99
        me.save()

    async def report_problem(self, msg, me):
        if me.conversation_flow is 7:
            await self.sender.forwardMessage(ADMINID,msg['message_id'])
            me.conversation_flow = 99
            me.save()
        else:
            await self.sender.sendMessage('De acuerdo, por favor, explica lo mejor'
                                          + ' que puedas el problema, indicando '
                                          + 'que querías hacer y que te ha '
                                          + 'respondido el bot exactamente, si es '
                                          + 'posible hazlo en un solo mensaje, si '
                                          + 'no tendrás que usar el comando '
                                          + 'reportar por cada mensaje que desees '
                                          + 'enviar')
            me.conversation_flow = 7
            me.save()

    async def check_register(self, username, password):
        return cyclos_api.auth(username, password)


if __name__ == "__main__":

    # create a delegator, it spawns a handler per request
    bot = telepot.aio.DelegatorBot(TOKEN, [
        pave_event_space()(
            per_chat_id(), create_open, BotHandler, timeout=TIMEOUT),
        ])

    loop = asyncio.get_event_loop()
    loop.create_task(bot.message_loop())
    logging.basicConfig(filename=LOG_DIR,
                        format='%(asctime)s - %(levelname)s:%(message)s',
                        level=DEBUG_LEVEL)
    logging.info("Listening")

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        # unfinished
        pass
