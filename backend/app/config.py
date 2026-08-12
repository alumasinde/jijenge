from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Kenya Services Platform"
    app_env: str = "development"
    app_debug: bool = False

    mysql_host: str
    mysql_port: int = 3306
    mysql_database: str
    mysql_user: str
    mysql_password: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    cors_origins: str = ""
    rate_limit_enabled: bool = True
    auth_rate_limit_per_minute: int = 10
    login_rate_limit_per_minute: int = 5
    register_rate_limit_per_minute: int = 5
    refresh_rate_limit_per_minute: int = 10

    mpesa_enabled: bool = False
    mpesa_consumer_key: str | None = None
    mpesa_consumer_secret: str | None = None
    mpesa_shortcode: str | None = None
    mpesa_passkey: str | None = None
    mpesa_callback_url: str | None = None
    mpesa_base_url: str = "https://sandbox.safaricom.co.ke"
    mpesa_timeout_seconds: float = 15.0
    mpesa_initiator_name: str | None = None
    mpesa_security_credential: str | None = None
    mpesa_result_url: str | None = None
    mpesa_transaction_type: str = "CustomerPayBillOnline"
    mpesa_b2c_command_id: str = "BusinessPayment"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


    def validate_runtime(self) -> None:
        if self.app_env.lower() in {"production", "prod"}:
            if self.app_debug:
                raise RuntimeError("APP_DEBUG must be false in production")
            if len(self.jwt_secret) < 32:
                raise RuntimeError("JWT_SECRET must be at least 32 characters in production")
            if not self.cors_origin_list:
                raise RuntimeError("CORS_ORIGINS must be explicitly configured in production")
            if "*" in self.cors_origin_list:
                raise RuntimeError("Wildcard CORS is not allowed in production")
            if self.mpesa_enabled:
                required = {
                    "MPESA_CONSUMER_KEY": self.mpesa_consumer_key,
                    "MPESA_CONSUMER_SECRET": self.mpesa_consumer_secret,
                    "MPESA_SHORTCODE": self.mpesa_shortcode,
                    "MPESA_PASSKEY": self.mpesa_passkey,
                    "MPESA_CALLBACK_URL": self.mpesa_callback_url,
                }
                missing = [key for key, value in required.items() if not value]
                if missing:
                    raise RuntimeError(
                        "M-Pesa is enabled but required configuration is missing: "
                        + ", ".join(missing)
                    )
                if not self.mpesa_callback_url.lower().startswith("https://"):
                    raise RuntimeError("MPESA_CALLBACK_URL must use HTTPS in production")


settings = Settings()
settings.validate_runtime()

