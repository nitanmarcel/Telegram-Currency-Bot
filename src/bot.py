import asyncio
import logging
import re
from asyncore import loop
from distutils.command.build import build
from math import ceil, log10

from telethon import TelegramClient, events

from config import API_HASH, API_ID, FIXER_KEY, FIXER_PLAN, BOT_TOKEN
from currencies import _currencies
from fixer import FixerClient, FixerError

logging.basicConfig(level=logging.INFO)

LOGGER = logging.getLogger('bot.py')
RESULT_FORMAT = '{} {} => {} {}'
RESULT_DATE_FORMAT = '**Mid-market exchange rate at ·** `{}`'
AMOUNT_FORMAT = '{:,.{}f}'
INLINE_TEXT_FORMAT = '{}\n{}'
with open('README', 'r') as f:
    ABOUT = f.read()

bot = TelegramClient('currbottg', api_id=API_ID, api_hash=API_HASH)
fixer = FixerClient(FIXER_KEY, FIXER_PLAN, error_logger=LOGGER)
bot.start(bot_token=BOT_TOKEN)

async def main(loop):
    loop.create_task(fixer.start_update())

    @bot.on(events.NewMessage(pattern=r'^/start'))
    async def _start(event):
        await event.reply(ABOUT, link_preview=False)

    @bot.on(events.InlineQuery)
    async def _convert(event):
        query = event.text
        builder = event.builder
        error = 'Invalid query!'

        if len(query.split()) >= 2 and query[0].isdigit():
            str_amount = re.sub(r'[^\d.]', '', query)
            if str_amount:
                str_no_amount = re.sub(str_amount, '', query).strip()
                from_currency = str_no_amount.split()[0].strip().upper()
                to_currency = str_no_amount.split()[-1].strip().upper()
                reversed_currencies = {y: x for x, y in _currencies.items()}
                if not all(x in _currencies.keys() for x in [from_currency, to_currency]):
                    reversed_currencies = {
                        y: x for x, y in _currencies.items()}
                    re_from_currency = re.compile(
                        re.escape(from_currency), re.IGNORECASE)
                    re_to_currency = re.compile(
                        re.escape(to_currency), re.IGNORECASE)
                    list_from_currency = list(
                        filter(re_from_currency.search, reversed_currencies))
                    list_to_currency = list(
                        filter(re_to_currency.search, reversed_currencies))
                    if from_currency not in _currencies.keys() and list_from_currency:
                        from_currency = reversed_currencies[list_from_currency[0]]
                    if to_currency not in _currencies.keys() and list_to_currency:
                        to_currency = reversed_currencies[list_to_currency[0]]
                if all(x in _currencies.keys() for x in [from_currency, to_currency]):
                    api = fixer.convert(str_amount, from_currency, to_currency)
                    if isinstance(api, FixerError):
                        error = api.message
                    else:
                        amount = api.amount
                        converted_amount = api.converted_amount
                        strf_date = api.date.strftime('%m/%d/%Y, %H:%M %Z')
                        amount_decimals = 2
                        converted_decimals = 2
                        if amount < 1:
                            amount_decimals = ceil(-log10(amount - int(amount))) + 1
                        if converted_amount < 1:
                            converted_decimals = ceil(
                                -log10(converted_amount - int(converted_amount))) + 1
                        amount = AMOUNT_FORMAT.format(amount, amount_decimals)
                        converted_amount = AMOUNT_FORMAT.format(
                            converted_amount, converted_decimals)
                        result = RESULT_FORMAT.format(
                            amount, from_currency, converted_amount, to_currency)
                        result_date = RESULT_DATE_FORMAT.format(
                            strf_date)
                        return await event.answer([builder.article(title=result, description=strf_date, text=INLINE_TEXT_FORMAT.format(result, result_date))])
        await event.answer([builder.article(title=error, text=error)], switch_pm ='Learn more', switch_pm_param='start')

    await bot.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
