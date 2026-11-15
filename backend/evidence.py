"""Keep extraction evidence as exact snippets with source line numbers."""

import re


def passages(text: str) -> list[dict]:
    return [
        {'line': number, 'text': sentence.strip()}
        for number, line in enumerate(text.splitlines(), start=1)
        for sentence in re.split(r'(?<=[.!?;])\s+', line)
        if sentence.strip()
    ]
