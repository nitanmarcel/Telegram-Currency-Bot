from .currencies import _currencies
from .types import Currency

from decimal import Decimal
from typing import List, Optional

import re

def parse_currency(query) -> Optional[Currency]:
    str_amount = re.sub(r'[^\d.]', '', query)
    str_no_amount = re.sub(str_amount, '', query).strip()
    if not str_no_amount:
        return
    from_currency = str_no_amount[:3].strip().upper()
    to_currency = str_no_amount[-3:].strip().upper()
    if from_currency in _currencies.keys() and to_currency in _currencies.keys():
        return Currency(from_currency, to_currency, Decimal(str_amount))

def format_currency(amount, currency):
    decimals = int(_currencies[currency][1])
    if amount < 1:
        _ = 1
        while amount < (_ := round(_ * 0.1, decimals)):
            decimals += 1
    return "{:.{}f}". format(amount, decimals)