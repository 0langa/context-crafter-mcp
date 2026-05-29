"""Core greeting logic."""


def greet(name: str, excited: bool = False) -> str:
    """Return a greeting for the given name."""
    msg = f"Hello, {name}!"
    return f"{msg}!!!" if excited else msg
