#!/usr/bin/env python3
"""Запуск анализатора выражений (лаб. 6): python main.py [выражение ...]"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"))

from lab6_expression_analyzer import analyze_expression, format_report  # noqa: E402


def main():
    if len(sys.argv) > 1:
        line = " ".join(sys.argv[1:]).strip()
    else:
        line = input("Выражение (одна строка): ").strip()
    if not line:
        print("Пустой ввод.")
        return
    print(format_report(analyze_expression(line)))


if __name__ == "__main__":
    main()
