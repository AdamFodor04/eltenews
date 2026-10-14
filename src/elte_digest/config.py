from dataclasses import dataclass
import os

DEFAULT_INDEX_URLS = (
    "https://www.elte.hu/hirek",
    "https://www.elte.hu/esemenyek",
    "https://www.elte.hu/interju",
    "https://www.elte.hu/palyazatok-felhivasok",
    "https://www.elte.hu/kozlemenyek",
    "https://www.elte.hu/sajto",
)


@dataclass(frozen=True)
class Settings:
    index_urls: tuple[str, ...] = DEFAULT_INDEX_URLS
    database_path: str = "data/digest.db"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    mail_from: str = ""
    mail_to: str = ""

    @classmethod
    def from_environment(cls) -> "Settings":
        def env(name: str, default: str) -> str:
            value = os.getenv(name, "").strip()
            return value or default

        return cls(
            index_urls=tuple(
                value.strip() for value in os.getenv("ELTE_INDEX_URLS", "").split(",")
                if value.strip()
            ) or cls.index_urls,
            database_path=env("ELTE_DATABASE_PATH", cls.database_path),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_base_url=env("OPENAI_BASE_URL", cls.openai_base_url).rstrip("/"),
            openai_model=env("OPENAI_MODEL", cls.openai_model),
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(env("SMTP_PORT", str(cls.smtp_port))),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            mail_from=os.getenv("MAIL_FROM", ""),
            mail_to=os.getenv("MAIL_TO", ""),
        )

    def validate_for_delivery(self) -> None:
        missing = [
            name for name, value in {
                "OPENAI_API_KEY": self.openai_api_key,
                "SMTP_HOST": self.smtp_host,
                "MAIL_FROM": self.mail_from,
                "MAIL_TO": self.mail_to,
            }.items() if not value
        ]
        if missing:
            raise RuntimeError("Missing required configuration: " + ", ".join(missing))
