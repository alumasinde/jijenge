import uuid
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException


MONEY = Decimal("0.01")


class CommissionService:
    """
    Calculates platform revenue from the final job price.
    It does not collect money merely because a provider applied.
    """

    def _get_rule(self, cursor, provider_id, category_id):
        cursor.execute(
            """
            SELECT
                cr.id,
                crt.code AS rule_type,
                cr.percentage_rate,
                cr.fixed_amount,
                cr.min_fee,
                cr.max_fee
            FROM commission_rules cr
            INNER JOIN commission_rule_types crt ON crt.id = cr.rule_type_id
            WHERE cr.is_active = 1
              AND cr.starts_at <= CURRENT_TIMESTAMP
              AND (cr.ends_at IS NULL OR cr.ends_at > CURRENT_TIMESTAMP)
              AND (
                    cr.provider_id = %s
                    OR cr.service_category_id = %s
                    OR (cr.provider_id IS NULL AND cr.service_category_id IS NULL)
                  )
            ORDER BY
                CASE
                    WHEN cr.provider_id = %s THEN 1
                    WHEN cr.service_category_id = %s THEN 2
                    ELSE 3
                END,
                cr.starts_at DESC,
                cr.id DESC
            LIMIT 1
            """,
            (provider_id, category_id, provider_id, category_id),
        )
        return cursor.fetchone()

    def calculate(self, gross_amount, rule):
        gross = Decimal(str(gross_amount))

        if gross < 0:
            raise ValueError("Gross amount cannot be negative")

        if rule["rule_type"] == "PERCENTAGE":
            fee = (
                gross
                * Decimal(str(rule["percentage_rate"]))
                / Decimal("100")
            )
        else:
            fee = Decimal(str(rule["fixed_amount"]))

        if rule["min_fee"] is not None:
            fee = max(fee, Decimal(str(rule["min_fee"])))

        if rule["max_fee"] is not None:
            fee = min(fee, Decimal(str(rule["max_fee"])))

        return fee.quantize(MONEY, rounding=ROUND_HALF_UP)

    def finalize_job_financials(
        self,
        assignment_id,
        processing_fee=Decimal("0.00"),
    ):
        # Lazy import: pure commission calculations can be tested without
        # requiring database configuration or a live MySQL connection.
        from app.database import db_connection

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)

            try:
                connection.start_transaction()

                cursor.execute(
                    """
                    SELECT
                        ja.id AS assignment_id,
                        ja.job_id,
                        ja.provider_id,
                        ja.execution_status_id,
                        j.customer_id,
                        j.service_category_id,
                        j.agreed_amount,
                        jes.code AS execution_status
                    FROM job_assignments ja
                    INNER JOIN jobs j ON j.id = ja.job_id
                    INNER JOIN job_execution_statuses jes
                        ON jes.id = ja.execution_status_id
                    WHERE ja.id = %s
                    FOR UPDATE
                    """,
                    (assignment_id,),
                )

                row = cursor.fetchone()

                if not row:
                    raise HTTPException(
                        status_code=404,
                        detail="Assignment not found",
                    )

                if row["execution_status"] != "COMPLETED":
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Financials can only be finalized after "
                            "customer confirmation"
                        ),
                    )

                cursor.execute(
                    """
                    SELECT id
                    FROM job_financial_breakdowns
                    WHERE assignment_id = %s
                    LIMIT 1
                    """,
                    (assignment_id,),
                )

                existing = cursor.fetchone()

                if existing:
                    connection.commit()
                    cursor.close()
                    return int(existing["id"])

                gross = Decimal(str(row["agreed_amount"]))

                rule = self._get_rule(
                    cursor,
                    int(row["provider_id"]),
                    int(row["service_category_id"]),
                )

                if not rule:
                    raise HTTPException(
                        status_code=409,
                        detail="No active platform commission rule exists",
                    )

                platform_fee = self.calculate(gross, rule)
                processing = Decimal(str(processing_fee)).quantize(MONEY)
                provider_net = gross - platform_fee - processing

                if provider_net < 0:
                    raise HTTPException(
                        status_code=409,
                        detail="Configured fees exceed the job amount",
                    )

                cursor.execute(
                    """
                    INSERT INTO job_financial_breakdowns
                        (
                            assignment_id,
                            job_id,
                            gross_amount,
                            platform_fee_amount,
                            provider_gross_amount,
                            payment_processing_fee,
                            provider_net_amount,
                            currency_code,
                            commission_rule_id,
                            finalized_at
                        )
                    VALUES
                        (
                            %s, %s, %s, %s, %s, %s, %s,
                            'KES', %s, CURRENT_TIMESTAMP
                        )
                    """,
                    (
                        assignment_id,
                        row["job_id"],
                        gross,
                        platform_fee,
                        gross - platform_fee,
                        processing,
                        provider_net,
                        rule["id"],
                    ),
                )

                breakdown_id = int(cursor.lastrowid)

                cursor.execute(
                    """
                    SELECT id
                    FROM provider_earning_statuses
                    WHERE code = 'AVAILABLE'
                    LIMIT 1
                    """
                )

                available_id = cursor.fetchone()["id"]

                cursor.execute(
                    """
                    INSERT INTO provider_earnings
                        (
                            public_id,
                            provider_id,
                            assignment_id,
                            financial_breakdown_id,
                            status_id,
                            gross_amount,
                            platform_fee_amount,
                            processing_fee_amount,
                            net_amount,
                            currency_code,
                            available_at
                        )
                    VALUES
                        (
                            %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, 'KES', CURRENT_TIMESTAMP
                        )
                    """,
                    (
                        str(uuid.uuid4()),
                        row["provider_id"],
                        assignment_id,
                        breakdown_id,
                        available_id,
                        gross,
                        platform_fee,
                        processing,
                        provider_net,
                    ),
                )

                cursor.execute(
                    """
                    INSERT INTO platform_revenue_entries
                        (
                            public_id,
                            assignment_id,
                            job_id,
                            entry_type_id,
                            amount,
                            currency_code,
                            financial_breakdown_id
                        )
                    SELECT
                        %s, %s, %s, id, %s, 'KES', %s
                    FROM platform_revenue_entry_types
                    WHERE code = 'JOB_COMMISSION'
                    LIMIT 1
                    """,
                    (
                        str(uuid.uuid4()),
                        assignment_id,
                        row["job_id"],
                        platform_fee,
                        breakdown_id,
                    ),
                )

                connection.commit()

            except Exception:
                connection.rollback()
                cursor.close()
                raise

            cursor.close()

        return breakdown_id
