"""CLI entry point for greeter."""

import argparse

from greeter.core import greet


def main() -> None:
    parser = argparse.ArgumentParser(description="Greet someone.")
    parser.add_argument("name", help="Name to greet.")
    parser.add_argument("--excited", action="store_true", help="Use excited punctuation.")
    args = parser.parse_args()
    print(greet(args.name, excited=args.excited))


if __name__ == "__main__":
    main()
