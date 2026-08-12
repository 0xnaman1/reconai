from recon_ai_core.settings import get_settings


def main() -> None:
    settings = get_settings()
    print(f"Recon AI worker configured for Redis at {settings.redis_url}")


if __name__ == "__main__":
    main()
