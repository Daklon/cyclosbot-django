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
from config import (TOKEN, TIMEOUT, DEBUG_LEVEL, LOG_DIR)
from bot.models import TelegramUser
from django.core.exceptions import ObjectDoesNotExist


class BotHandler(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(BotHandler, self).__init__(*args, **kwargs)
        self.flow = {0: self.wait_username, 1: self.wait_password, }
        self.entry_point = {'saldo': self.account_balance, 'ayuda': self.send_help}

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

    async def register(self, msg, this_chat_id):
        me = TelegramUser(chat_id=this_chat_id, conversation_flow=0)
        me.save()
        await self.sender.sendMessage('No estás registrado, vamos a'
                                      + ' solucionarlo, primero dime '
                                      + ' tu usuario de la web')

    async def process(self, msg, me):
        if (me.conversation_flow < 2):
            await self.flow[me.conversation_status](msg, me)
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
                                          + 'través de mi')
            me.conversation_flow = 2
            me.save()
            await self.send_help(self, msg, me)
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
        await self.sender.sendMessage('Esta es la ayuda')

    async def account_balance(self, msg, me):
        logging.debug("Waiting api answer")
        data = cyclos_api.get_account_balance(me.username, me.password)
        logging.debug("Received api answer")
        logging.info("Sending answer to: %s", me.chat_id)

        await self.sender.sendMessage('Saldo: ' + data['balance'] +
                                      '\nCrédito disponible: ' +
                                      data['availableBalance'])

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
