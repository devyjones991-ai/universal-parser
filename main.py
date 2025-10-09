"""Точка входа приложения."""
import asyncio

from bot import start_bot


def main() -> None:
    print("🚦 Universal Parser стартует...")
    asyncio.run(start_bot())


if __name__ == "__main__":
    main()
