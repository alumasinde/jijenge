from decimal import Decimal, ROUND_HALF_UP

from app.database import db_connection


MONEY = Decimal("0.01")


class FeeService:
    def calculate(self, fee_code: str, base_amount: Decimal) -> Decimal:
        if base_amount < 0:
            raise ValueError("Base amount cannot be negative")

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT calculation_type, rate, fixed_amount
                FROM fee_types
                WHERE code = %s
                  AND is_active = 1
                LIMIT 1
                """,
                (fee_code,),
            )
            row = cursor.fetchone()
            cursor.close()

        if not row:
            raise ValueError("Fee configuration not found")

        if row["calculation_type"] == "PERCENTAGE":
            result = base_amount * (Decimal(row["rate"]) / Decimal("100"))
        elif row["calculation_type"] == "FIXED":
            result = Decimal(row["fixed_amount"] or 0)
        else:
            raise ValueError("Unsupported fee calculation type")

        return result.quantize(MONEY, rounding=ROUND_HALF_UP)
