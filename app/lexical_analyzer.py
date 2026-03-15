class LexicalAnalyzer:
    def __init__(self):
        self.keywords = {
            "for":   "ключевое слово",
            "in":    "ключевое слово",
            "print": "ключевое слово",
        }
        self.operators = {
            ":": "оператор диапазона",
            "=": "оператор присваивания",
        }
        self.separators = {
            "(": "разделитель",
            ")": "разделитель",
            "{": "разделитель",
            "}": "разделитель",
            ";": "конец оператора",
        }

    def analyze(self, text: str):
        tokens = []
        errors = []
        i = 0
        n = len(text)
        line_num = 1
        char_pos = 1   

        while i < n:
            ch = text[i]
            start_line = line_num
            start_pos = char_pos

            # Пробелы, табуляция, перевод строки
            if ch.isspace():
                code = 11
                if ch == ' ':
                    lexeme = "(пробел)"
                    token_type = "разделитель (пробел)"
                elif ch == '\n':
                    lexeme = "(перевод строки)"
                    token_type = "разделитель (перевод строки)"
                    line_num += 1
                    char_pos = 0
                elif ch == '\t':
                    lexeme = "(табуляция)"
                    token_type = "разделитель (табуляция)"
                else:
                    lexeme = "(пробел)"
                    token_type = "разделитель (пробел)"

                tokens.append({
                    'code': code,
                    'type': token_type,
                    'lexeme': lexeme,
                    'location': f"строка {start_line},{start_pos}-{char_pos}"
                })
                i += 1
                char_pos += 1
                continue

            # Идентификатор
            if ch.isalpha() or ch == '_':
                lexeme = ''
                while i < n and (text[i].isalnum() or text[i] == '_'):
                    lexeme += text[i]
                    i += 1
                    char_pos += 1
                token_type = self.keywords.get(lexeme, "идентификатор")
                code = 14 if lexeme in self.keywords else 2
                tokens.append({
                    'code': code,
                    'type': token_type,
                    'lexeme': lexeme,
                    'location': f"строка {start_line},{start_pos}-{char_pos-1}"
                })
                continue

            # Целое число
            if ch.isdigit():
                lexeme = ''
                while i < n and text[i].isdigit():
                    lexeme += text[i]
                    i += 1
                    char_pos += 1
                tokens.append({
                    'code': 1,
                    'type': "целое без знака",
                    'lexeme': lexeme,
                    'location': f"строка {start_line},{start_pos}-{char_pos-1}"
                })
                continue

            # Оператор
            if ch in self.operators:
                tokens.append({
                    'code': 10,
                    'type': self.operators[ch],
                    'lexeme': ch,
                    'location': f"строка {start_line},{start_pos}-{char_pos}"
                })
                i += 1
                char_pos += 1
                continue

            if ch in self.separators:
                tokens.append({
                    'code': 16,
                    'type': self.separators[ch],
                    'lexeme': ch,
                    'location': f"строка {start_line},{start_pos}-{char_pos}"
                })
                i += 1
                char_pos += 1
                continue

            errors.append((line_num, char_pos, f"Недопустимый символ '{ch}'"))
            i += 1
            char_pos += 1

        return tokens, errors