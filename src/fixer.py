import asyncio
import logging
from cmath import log10
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from math import ceil

from aiohttp import ClientSession

@dataclass
class FixerError:
    message: str = ''
    code: int = 0


@dataclass
class Currency:
    amount: Decimal = Decimal(0)
    converted_amount: Decimal = Decimal(0)
    from_currency: str = ''
    to_currency: str = ''
    date: datetime = 0


class FixerClient:
    def __init__(self, access_key, access_type, error_logger=None):
        self._cached_result = {}
        self._base_url = 'http://data.fixer.io/api/latest'
        self._params = {'access_key': access_key}
        self._access_type = access_type
        self._error_logger = error_logger
        if access_type == 'professional':
            self._update_time_multiplier = 10
        elif access_type == 'professional plus':
            self._update_time_multiplier = 1
        else:
            self._update_time_multiplier = 60
        self._update_time = 60 * self._update_time_multiplier

    async def start_update(self):
        # Free plan not supported.
        if self._access_type == 'free':
            return
        await self._start_update()

    async def _start_update(self):
        while True:
            async with ClientSession() as session:
                async with session.get(self._base_url, params=self._params) as response:
                    if response.status != 200:
                        pass
                    js = await response.json()
                    if not js['success']:
                        if self._error_logger:
                            self._error_logger.info('{} - {}'.format(js['error']['type'], js['error']['info']))
                        break
                    self._cached_result = js
            last_update = datetime.fromtimestamp(
                self._cached_result['timestamp'])
            await asyncio.sleep(self._update_time - (datetime.now() - last_update).seconds)

    @property
    def rates(self):
        if self._cached_result:
            return self._cached_result['rates']
        return None

    def convert(self, amount, from_currency, to_currency):
        if not self._cached_result:
            return FixerError(message='No fixer data cached.', code=404)
        amount = Decimal(amount)
        from_rate = self.rates[from_currency]
        to_rate = self.rates[to_currency]
        update_date = datetime.fromtimestamp(
            self._cached_result['timestamp']).replace(tzinfo=timezone.utc)
        return Currency(amount=amount, converted_amount=amount / Decimal(from_rate) * Decimal(to_rate), from_currency=from_currency, to_currency=to_currency, date=update_date)
