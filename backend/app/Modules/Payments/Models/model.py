from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PaymentIntent:
    id: int
    public_id: str
    payer_user_id: int
    amount: Decimal
    currency_code: str
    status: str
    payment_method: str
