#!/usr/bin/env python

import io
import logging
import os
import tempfile

from telegram import Bot, ChatAction, Document, File, Message, Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

import local_settings as settings
# Enable logging
from tools import filter_and_add_da

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


class Commands(object):
    @classmethod
    def check_permission(cls, bot: Bot, update: Update):
        if settings.TELEGRAM_BOT_AVAILABLE in (False, True):
            return settings.TELEGRAM_BOT_AVAILABLE
        return update.effective_user.id in settings.TELEGRAM_BOT_AVAILABLE

    @classmethod
    def permission_denied(cls, bot: Bot, update: Update):
        update.message.reply_text('Permission denied!')

    @classmethod
    def start(cls, bot: Bot, update: Update):
        if not cls.check_permission(bot, update):
            return cls.permission_denied(bot, update)
        update.message.reply_text('Hello! Send me a CSV-file!')

    @classmethod
    def help(cls, bot: Bot, update: Update):
        if not cls.check_permission(bot, update):
            return cls.permission_denied(bot, update)
        update.message.reply_text('Help!')

    @classmethod
    def csv_document(cls, bot: Bot, update: Update):
        if not cls.check_permission(bot, update):
            return cls.permission_denied(bot, update)
        assert isinstance(update.message, Message)
        update.message.reply_text('Relax for a while ;) processing the file...', quote=True)
        bot.send_chat_action(update.message.chat_id, ChatAction.UPLOAD_DOCUMENT)
        assert isinstance(update.message.document, Document)
        file = bot.get_file(update.message.document.file_id)
        assert isinstance(file, File)
        bytes_file_in = io.BytesIO()
        file_out = io.StringIO()
        file.download(out=bytes_file_in)
        bytes_file_in.seek(0)
        file_in = io.StringIO()
        file_in.write(bytes_file_in.read().decode())
        file_in.seek(0)
        file_out = tempfile.NamedTemporaryFile('w+', delete=False)
        name = '.'.join(os.path.basename(file.file_path).split('.')[:-1]) or 'your'

        filter_and_add_da(file_in, file_out)

        path = file_out.name
        file_out.close()
        file_in.close()
        filename = name + '_result.csv'
        file = open(path, 'rb')
        update.message.reply_document(file, filename=filename, caption='Finished, my boss!', quote=True)
        file.close()
        os.remove(path)

    @classmethod
    def all(cls, bot: Bot, update: Update):
        if not cls.check_permission(bot, update):
            return cls.permission_denied(bot, update)
        update.message.reply_text('Cannot process message!')

    @classmethod
    def log_all(cls, bot: Bot, update: Update):
        logger.info('{} sent {} in chat {}'.format(update.effective_user, update.effective_message, update.effective_chat))

    @classmethod
    def error(cls, bot: Bot, update: Update, error):
        logger.warning('Update "%s" caused error "%s"' % (update, error))


# noinspection PyProtectedMember
class CsvDocument(Filters._Document):
    def filter(self, message: Message):
        return super().filter(message) and message.document.mime_type == 'text/csv'


def main():
    updater = Updater(settings.TELEGRAM_BOT_TOKEN, workers=1)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', Commands.start))
    dp.add_handler(CommandHandler('help', Commands.help))

    dp.add_handler(MessageHandler(CsvDocument(), Commands.csv_document))
    dp.add_handler(MessageHandler(Filters.all, Commands.all))
    dp.add_handler(MessageHandler(Filters.all, Commands.log_all), group=100)

    dp.add_error_handler(Commands.error)

    updater.start_polling(timeout=300, allowed_updates=['message'])
    updater.idle()


if __name__ == '__main__':
    main()
