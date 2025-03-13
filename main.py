import sys
import re
import os

multilineCommentMode = False

identificatorLen = 20

maxInt = 2 ** 31 - 1
minInt = -2 ** 31

operators = {
    "==": "Relational operation",
    "!=": "Relational operation",
    "<=": "Relational operation",
    ">=": "Relational operation",
    "<": "Relational operation",
    ">": "Relational operation",
    "+": "Arithmetic operator",
    "-": "Arithmetic operator",
    "/": "Arithmetic operator",
    "*": "Arithmetic operator",
    "=": "Assignment operator",
}

separators = {
    "(": "Parenthesis bracket",
    ")": "Parenthesis bracket",
    "[": "Square bracket",
    "]": "Square bracket",
    "{": "Curly bracket",
    "}": "Curly bracket",
    ":": "Colon separator",
    ",": "Comma separator",
    ";": "Semicolon separator",
    ".": "Dot",
}

keywords = {
    "and": "Keyword",
    "as": "Keyword",
    "break": "Keyword",
    "class": "Keyword",
    "continue": "Keyword",
    "def": "Keyword",
    "elif": "Keyword",
    "else": "Keyword",
    "finally": "Keyword",
    "for": "Keyword",
    "from": "Keyword",
    "if": "Keyword",
    "import": "Keyword",
    "in": "Keyword",
    "not": "Keyword",
    "or": "Keyword",
    "return": "Keyword",
    "try": "Keyword",
    "while": "Keyword",
    "with": "Keyword",
    "bool": "Keyword",
    "int": "Keyword",
    "char": "Keyword",
    "string": "Keyword",
    "str": "Keyword",
    "true": "Keyword",
    "false": "Keyword",
    "double": "Keyword",
}

nums = {
    r'\d*\.?\d+[eE][-+]?\d+\b': "Exponential number",
    r'\d*\.\d+([eE][-+]?\d+)?\b': "Float number",
    r'0[0-7]+\b': "Octal number",
    r'\d+\b': "Integer number",
    r'0b[01]+\b': "Binary number",
    r'0x[0-9a-fA-F]+\b': "Hexadecimal number",
}


class Token:
    def __init__(self, item, key, line, position):
        self.item = item
        self.key = key
        self.line = line
        self.position = position


def isString(item):
    return (len(item) > 1 and
            (item.startswith("\"") and item.endswith("\"") and item.count("\"") % 2 == 0) or
            (item.startswith("\'") and item.endswith("\'") and item.count("\'") % 2 == 0))

def processString(input_string):
    return input_string.replace("\n", "\\n")

def isValidIdentificator(item):
    if not (item[0].isalpha() or (item[0] == "_" and len(item) > 1)):
        return False

    if len(item) > identificatorLen:
        return False

    if not all(c.isdigit() or c == "_" or 'a' <= c <= 'z' or 'A' <= c <= 'Z' for c in item):
        return False

    return True


def readDigit(line):
    item = ""
    for char in line:
        if item == "." and not char.isdigit():
            return item

        if char != " ":
            item += char
        else:
            break

    return item

def readString(lines, lineIdx, position):
    quote_char = lines[lineIdx][position]
    item = quote_char
    position += 1

    while lineIdx < len(lines):
        line = lines[lineIdx]
        for char in line[position:]:
            item += char
            position += 1

            if char == quote_char:
                return item, lineIdx

        if position >= len(line):
            item += '\n'
            lineIdx += 1
            position = 0


    if lineIdx >= len(lines):
        item = item[:-1]
    return item, lineIdx


def readIdentifier(line):
    item = ""
    for char in line:
        if char.isalnum() or char == "_":
            item += char
        else:
            break
    return item


def readOperator(line):
    for op in sorted(operators.keys(), key=len, reverse=True):
        if line.startswith(op):
            return op
    return None


def makeToken(line, lineIdx, position):
    global multilineCommentMode
    global multiStringMode
    item = ""

    for i, char in enumerate(line):
        if multilineCommentMode:
            if char == "*" and i + 1 < len(line) and line[i + 1] == "/":
                multilineCommentMode = False
                return Token("*/", "MultiComment End", lineIdx, position + i)
            else:
                return None
        else:
            if char == "/":
                if i + 1 < len(line):
                    next_char = line[i + 1]
                    if next_char == "/":
                        return Token(line[i:], "Single Comment", lineIdx, position + i)
                    elif next_char == "*":
                        multilineCommentMode = True
                        return Token("/*", "MultiComment Start", lineIdx, position + i)

            elif char.isdigit() or char == ".":
                item = readDigit(line[i:])
                matched = False
                for key, value in nums.items():
                    if re.fullmatch(key, item):
                        matched = True
                        if value == "Integer number":
                            num = int(item)
                            if num < minInt or num > maxInt:
                                return Token(item, "Error", lineIdx, position + i)
                        return Token(item, value, lineIdx, position + i)
                if not matched:
                    if item == ".":
                        return Token(char, separators[item], lineIdx, position + i)
                    return Token(item, "Error", lineIdx, position + i)

            elif char in ["'", '"']:
                item = readString(line[i:])
                if isString(item):
                    return Token(item, "String", lineIdx, position + i)
                return Token(item, "Error", lineIdx, position + i)

            elif char.isalpha() or char == "_":
                item = readIdentifier(line[i:])
                if item in keywords:
                    return Token(item, "Keyword", lineIdx, position + i)
                if isValidIdentificator(item):
                    return Token(item, "Identificator", lineIdx, position + i)
                return Token(item, "Error", lineIdx, position + i)

            elif char in separators:
                return Token(char, separators[char], lineIdx, position + i)

            elif char in operators or char == "!":
                item = readOperator(line[i:])
                if item:
                    return Token(item, operators.get(item, "Error"), lineIdx, position + i)

    return Token(item, "Error", lineIdx, position)


def parseLine(lines, line, lineIdx, outFile, position):
    position = position + 0
    global multilineCommentMode
    while position < len(line):
        char = line[position]
        if char != " ":
            startLineIdx = lineIdx
            startPosition = position
            if char == "'" or char == '"' and not multilineCommentMode:
                item, lineIdx = readString(lines, lineIdx, position)
                if isString(item):
                    token = Token(processString(item), "String", lineIdx, position)
                else:
                    token = Token(processString(item), "Error", lineIdx, position)
            else:
                token = makeToken(line[position:], lineIdx, position)

            if token is not None:
                if token.key == "Error" or token.key == "String":
                    outFile.write(f"{token.key}: {token.item} [{startLineIdx+1}, {startPosition}]\n")
                elif token.item != "/*" and token.item != "*/" and token.key != "Single Comment":
                    outFile.write(f"{token.key}: {token.item} [{token.line+1}, {token.position}]\n")

                position += len(token.item)

                if token.key == "String" and token.item.rfind('\\n') != -1:
                    position = len(token.item) - token.item.rfind('\\n') - 2
                    parseLine(lines, lines[lineIdx], lineIdx, outFile, position)

            else:
                position += 1
        else:
            position += 1

    return lineIdx

def lexer(inputFile, outputFile):
    global multilineCommentMode

    with open(inputFile, "r") as inFile:
        lines = [line.rstrip('\n') for line in inFile]

    outFile = open(outputFile, "w")
    if os.stat(inputFile).st_size == 0:
        outFile.write(f"Input file is empty\n")
        return

    lineIdx = 1
    for i in range(0, len(lines)):
        if lineIdx < len(lines):
            lineIdx = parseLine(lines, lines[lineIdx].rstrip('\n'), lineIdx, outFile, 0)
            lineIdx += 1

    if multilineCommentMode:
        outFile.write(f"Error: non closed multiline comment\n")

    return


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Invalid arguments len")
        sys.exit()

    inputFile = sys.argv[1]
    outputFile = sys.argv[2]

    lexer(inputFile, outputFile)