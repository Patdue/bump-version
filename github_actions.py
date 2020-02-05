import os


def set_output(name: str, value: str) -> None:
    print(f'::set-output name={name}::{value}')


def get_input(name: str) -> str:
    return os.environ.get(f'INPUT_{name.upper()}')