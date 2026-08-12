import base64
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import httpx

from app.Modules.Payments.Providers.base import (
    PaymentProvider, ProviderPaymentResult, ProviderRequestResult
)


class MpesaProvider(PaymentProvider):
    """
    Safaricom Daraja adapter.

    References:
    - OAuth
    - STK Push
    - STK Query
    - B2C payout

    Actual production credentials must be supplied through configuration.
    """

    code = "MPESA"

    def __init__(self, config):
        self.config = config

    def _enabled(self):
        return bool(
            getattr(self.config, "mpesa_enabled", False)
            and getattr(self.config, "mpesa_consumer_key", None)
            and getattr(self.config, "mpesa_consumer_secret", None)
            and getattr(self.config, "mpesa_shortcode", None)
            and getattr(self.config, "mpesa_passkey", None)
            and getattr(self.config, "mpesa_callback_url", None)
        )

    def _base_url(self):
        return getattr(
            self.config, "mpesa_base_url",
            "https://sandbox.safaricom.co.ke"
        ).rstrip("/")

    def _timeout(self):
        return float(getattr(self.config, "mpesa_timeout_seconds", 15.0))

    def _timestamp(self):
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def _password(self, timestamp):
        raw=(
            str(self.config.mpesa_shortcode)
            + str(self.config.mpesa_passkey)
            + timestamp
        ).encode()
        return base64.b64encode(raw).decode()

    def _phone(self, value):
        value=str(value).strip().replace(" ","").replace("+","")
        if value.startswith("0"):
            value="254"+value[1:]
        if not value.startswith("254"):
            raise ValueError("Phone number must be Kenyan format")
        if len(value)!=12 or not value.isdigit():
            raise ValueError("Invalid Kenyan phone number")
        if value[3] not in "712":
            raise ValueError("Unsupported Kenyan mobile number")
        return value

    def _token(self):
        if not self._enabled():
            raise RuntimeError("M-Pesa is disabled or incompletely configured")

        credentials=(
            f"{self.config.mpesa_consumer_key}:"
            f"{self.config.mpesa_consumer_secret}"
        )
        encoded=base64.b64encode(credentials.encode()).decode()

        url=(
            f"{self._base_url()}/oauth/v1/generate"
            "?grant_type=client_credentials"
        )
        with httpx.Client(timeout=self._timeout()) as client:
            response=client.get(
                url,
                headers={"Authorization":f"Basic {encoded}"},
            )
        response.raise_for_status()
        data=response.json()
        token=data.get("access_token")
        if not token:
            raise RuntimeError("Daraja OAuth response did not contain access_token")
        return token

    def _post(self,path,payload):
        token=self._token()
        url=f"{self._base_url()}{path}"
        with httpx.Client(timeout=self._timeout()) as client:
            response=client.post(
                url,
                json=payload,
                headers={
                    "Authorization":f"Bearer {token}",
                    "Content-Type":"application/json",
                },
            )
        response.raise_for_status()
        return response.json()

    def initiate_customer_payment(
        self, *, amount: Decimal, currency_code: str,
        payer_reference: str, callback_url: str, idempotency_key: str
    ):
        if currency_code != "KES":
            raise ValueError("M-Pesa supports KES for this integration")

        amount_int=int(
            Decimal(str(amount)).quantize(
                Decimal("1"),rounding=ROUND_HALF_UP
            )
        )
        if amount_int<=0:
            raise ValueError("M-Pesa amount must be greater than zero")

        phone=self._phone(payer_reference)
        timestamp=self._timestamp()

        payload={
            "BusinessShortCode":int(self.config.mpesa_shortcode),
            "Password":self._password(timestamp),
            "Timestamp":timestamp,
            "TransactionType":getattr(
                self.config,"mpesa_transaction_type",
                "CustomerPayBillOnline"
            ),
            "Amount":amount_int,
            "PartyA":int(phone),
            "PartyB":int(self.config.mpesa_shortcode),
            "PhoneNumber":int(phone),
            "CallBackURL":callback_url,
            "AccountReference":idempotency_key[:80],
            "TransactionDesc":"Service platform payment",
        }

        data=self._post("/mpesa/stkpush/v1/processrequest",payload)
        response_code=str(data.get("ResponseCode",""))

        if response_code != "0":
            return ProviderRequestResult(
                status="FAILED",
                provider_request_id=data.get("MerchantRequestID"),
                provider_reference=data.get("CheckoutRequestID"),
                response=data,
                message=data.get("ResponseDescription") or "STK Push rejected",
            )

        return ProviderRequestResult(
            status="SENT",
            provider_request_id=data.get("MerchantRequestID"),
            provider_reference=data.get("CheckoutRequestID"),
            response=data,
            message=data.get("CustomerMessage"),
        )

    def query_stk(self, checkout_request_id):
        timestamp=self._timestamp()
        payload={
            "BusinessShortCode":int(self.config.mpesa_shortcode),
            "Password":self._password(timestamp),
            "Timestamp":timestamp,
            "CheckoutRequestID":checkout_request_id,
        }
        return self._post("/mpesa/stkpushquery/v1/query",payload)

    def request_payout(
        self, *, amount: Decimal, currency_code: str,
        payout_reference: str, destination_reference: str,
        idempotency_key: str
    ):
        if not getattr(self.config,"mpesa_initiator_name",None):
            raise RuntimeError("M-Pesa B2C initiator is not configured")
        if not getattr(self.config,"mpesa_security_credential",None):
            raise RuntimeError("M-Pesa B2C security credential is not configured")
        if currency_code!="KES":
            raise ValueError("M-Pesa B2C supports KES for this integration")

        phone=self._phone(destination_reference)
        amount_int=int(Decimal(str(amount)).quantize(Decimal("1")))
        payload={
            "InitiatorName":self.config.mpesa_initiator_name,
            "SecurityCredential":self.config.mpesa_security_credential,
            "CommandID":getattr(
                self.config,"mpesa_b2c_command_id","BusinessPayment"
            ),
            "Amount":amount_int,
            "PartyA":int(self.config.mpesa_shortcode),
            "PartyB":int(phone),
            "Remarks":payout_reference[:100],
            "QueueTimeOutURL":self.config.mpesa_result_url,
            "ResultURL":self.config.mpesa_result_url,
            "Occasion":idempotency_key[:100],
        }
        data=self._post("/mpesa/b2c/v1/paymentrequest",payload)
        code=str(data.get("ResponseCode",""))
        return ProviderRequestResult(
            status="SENT" if code=="0" else "FAILED",
            provider_request_id=data.get("ConversationID"),
            provider_reference=data.get("OriginatorConversationID"),
            response=data,
            message=data.get("ResponseDescription"),
        )

    def request_refund(self, **kwargs):
        raise NotImplementedError(
            "Use the configured Safaricom reversal/refund product and approval workflow"
        )

    def verify_callback(self, payload: dict, headers: dict[str,str]) -> bool:
        # Safaricom STK callbacks do not provide a generic application signature
        # that can be verified here. Structural validation plus matching the
        # provider reference and amount happens before financial finalization.
        body=payload.get("Body")
        callback=body.get("stkCallback") if isinstance(body,dict) else None
        return bool(
            isinstance(callback,dict)
            and callback.get("CheckoutRequestID")
            and callback.get("MerchantRequestID")
            and callback.get("ResultCode") is not None
        )

    def parse_callback(self, payload: dict[str,Any]):
        callback=payload["Body"]["stkCallback"]
        result_code=int(callback["ResultCode"])
        metadata=callback.get("CallbackMetadata",{}).get("Item",[]) or []
        values={
            item.get("Name"):item.get("Value")
            for item in metadata
            if isinstance(item,dict) and item.get("Name")
        }
        receipt=values.get("MpesaReceiptNumber")
        amount=values.get("Amount")
        status="SUCCEEDED" if result_code==0 else "FAILED"
        return ProviderPaymentResult(
            status=status,
            provider_transaction_id=receipt or callback.get("CheckoutRequestID"),
            provider_reference=callback.get("CheckoutRequestID"),
            amount=Decimal(str(amount)) if amount is not None else None,
            currency_code="KES",
            message=callback.get("ResultDesc"),
        )
