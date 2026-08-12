from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LedgerLine:
    account_id: int
    debit: Decimal
    credit: Decimal
