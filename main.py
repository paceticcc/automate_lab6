import sys
import re


class Token:
    def __init__(self, type_, lexeme, line, column):
        self.type = type_
        self.lexeme = lexeme
        self.line = line
        self.column = column

    def __str__(self):
        return f"{self.type} ({self.line}, {self.column}) \"{self.lexeme}\""


class PascalLexer:
    KEYWORDS = {
        "array": "ARRAY",
        "begin": "BEGIN",
        "else": "ELSE",
        "end": "END",
        "if": "IF",
        "of": "OF",
        "or": "OR",
        "program": "PROGRAM",
        "procedure": "PROCEDURE",
        "then": "THEN",
        "type": "TYPE",
        "var": "VAR"
    }

    OPERATORS = {
        "*": "MULTIPLICATION",
        "+": "PLUS",
        "-": "MINUS",
        "/": "DIVIDE",
        ";": "SEMICOLON",
        ",": "COMMA",
        "(": "LEFT_PAREN",
        ")": "RIGHT_PAREN",
        "[": "LEFT_BRACKET",
        "]": "RIGHT_BRACKET",
        "=": "EQ",
        ">": "GREATER",
        "<": "LESS",
        "<=": "LESS_EQ",
        ">=": "GREATER_EQ",
        "<>": "NOT_EQ",
        ":": "COLON",
        ":=": "ASSIGN",
        ".": "DOT"
    }

    def __init__(self, input_file):
        self.input_file = open(input_file, 'r')
        self.current_line = 0
        self.current_column = 0
        self.buffer = ""
        self.eof = False

    def close(self):
        self.input_file.close()

    def read_next_line(self):
        self.buffer = self.input_file.readline()

        if not self.buffer:  # EOF
            self.eof = True
            self.buffer = ""
        else:
            self.current_line += 1
        self.current_column = 1

    def next_token(self):
        while not self.eof or self.buffer:
            if not self.buffer:
                self.read_next_line()
                if self.eof:
                    return None

            while self.buffer and self.buffer[0].isspace():
                self.buffer = self.buffer[1:]
                self.current_column += 1

            if not self.buffer:
                continue

            self.current_column += len(self.buffer) - len(self.buffer.lstrip())

            if self.buffer.startswith("//"):
                self.buffer = ""
                continue

            if self.buffer.startswith("{"):
                temp = ""
                temp += self.buffer.replace("\n", "")
                start_line = self.current_line
                start_column = self.current_column
                while True:

                    end_index = self.buffer.find("}")

                    if end_index != -1:
                        self.buffer = self.buffer[end_index + 1:]
                        self.current_column += end_index + 1
                        break
                    else:
                        self.read_next_line()
                        if self.eof:
                            bad_token = Token("BAD", temp, start_line, start_column)
                            self.buffer = ""
                            return bad_token
                        else:
                            temp += "\n" + self.buffer.replace("\n", "")

                continue

            if self.buffer.startswith("'"):
                string_start = self.buffer
                match = re.match(r"'(.*?)'", self.buffer)
                if match:
                    lexeme = match.group(0)
                    token = Token("STRING", lexeme, self.current_line, self.current_column)
                    self.buffer = self.buffer[len(lexeme):]
                    self.current_column += len(lexeme)
                    return token
                else:
                    string_start = string_start.replace("\n", "")
                    bad_token = Token("BAD", string_start, self.current_line, self.current_column)
                    self.buffer = ""
                    return bad_token

            match = re.match(r"\d+(\.)?(\d+)?([eE][+-]?\d+)?", self.buffer)
            if match:
                lexeme = match.group(0)

                if "." in lexeme and match.group(2) is None:  # No digits after the point
                    bad_token = Token("BAD", lexeme, self.current_line, self.current_column)
                    self.buffer = self.buffer[len(lexeme):]
                    self.current_column += len(lexeme)
                    return bad_token

                if lexeme.isdigit() and len(lexeme) > 16:
                    bad_token = Token("BAD", lexeme, self.current_line, self.current_column)
                    self.buffer = self.buffer[len(lexeme):]
                    self.current_column += len(lexeme)
                    return bad_token

                if len(self.buffer) > len(lexeme) and not re.match(r"[ \t\n\(\)\+\-\*/;,=\[\]{}<>'.:0-9]",
                                                                   self.buffer[len(lexeme):][0]):
                    match = re.match(r"[a-zA-Z0-9_]*", self.buffer)
                    bad_token = Token("BAD", match.group(0), self.current_line, self.current_column)
                    self.buffer = self.buffer[len(match.group(0)):]
                    self.current_column += len(match.group(0))
                    return bad_token

                token_type = "FLOAT" if "." in lexeme or "e" in lexeme.lower() else "INTEGER"
                token = Token(token_type, lexeme, self.current_line, self.current_column)
                self.buffer = self.buffer[len(lexeme):]
                self.current_column += len(lexeme)
                return token

            match = re.match(r"[a-zA-Z_][a-zA-Z0-9_]*", self.buffer)
            if match:
                lexeme = match.group(0)

                if len(lexeme) > 256:
                    bad_token = Token("BAD", lexeme, self.current_line, self.current_column)
                    self.buffer = self.buffer[len(lexeme):]
                    self.current_column += len(lexeme)
                    return bad_token

                token_type = self.KEYWORDS.get(lexeme.lower(), "IDENTIFIER")
                token = Token(token_type, lexeme, self.current_line, self.current_column)
                self.buffer = self.buffer[len(lexeme):]
                self.current_column += len(lexeme)
                self.buffer = self.buffer.replace("\n", "")

                if self.buffer and not re.match(r"[ \t\(\)\+\-\*/;,=\[\]{}<>'.:]", self.buffer[0]) and not re.match(
                        r"^[a-zA-Z0-9_]*$", self.buffer):
                    self.current_column -= len(lexeme)
                    bad_token = Token("BAD", lexeme + self.buffer, self.current_line, self.current_column)
                    self.buffer = ""
                    return bad_token

                return token

            for op, token_type in sorted(self.OPERATORS.items(), key=lambda x: -len(x[0])):
                if self.buffer.startswith(op):
                    token = Token(token_type, op, self.current_line, self.current_column)
                    self.buffer = self.buffer[len(op):]
                    self.current_column += len(op)
                    return token

            if not re.match(r"^[a-zA-Z0-9_]*$", self.buffer):
                match = re.match(r"[^ \t\n\(\)\+\-\*/;,=\[\]{}<>'.:]*", self.buffer)

                print(match.group(0))
                self.buffer = self.buffer[len(match.group(0)):]
                bad_token = Token("BAD", match.group(0), self.current_line, self.current_column)
                self.current_column += len(match.group(0))
                return bad_token

        return None


def main():
    if len(sys.argv) != 3:
        print("Usage: python PascalLexer.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    lexer = PascalLexer(input_file)

    with open(output_file, 'w') as output:
        while True:
            token = lexer.next_token()
            if token is None:
                break
            print(token)
            output.write(str(token) + '\n')

    lexer.close()


if __name__ == "__main__":
    main()