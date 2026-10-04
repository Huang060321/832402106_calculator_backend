"""Safe mathematical expression tokenizer and recursive-descent parser.

User input is parsed as mathematical syntax. It is never passed to eval, exec,
or any general-purpose code execution facility.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


class CalculationError(ValueError):
    """An expression cannot be safely evaluated."""


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    position: int


class Tokenizer:
    """Convert a small mathematical language into tokens."""

    MAX_EXPRESSION_LENGTH = 200

    def __init__(self, source: str) -> None:
        self.source = source

    def tokenize(self) -> list[Token]:
        if not self.source or not self.source.strip():
            raise CalculationError("表达式不能为空")
        if len(self.source) > self.MAX_EXPRESSION_LENGTH:
            raise CalculationError("表达式不能超过 200 个字符")

        tokens: list[Token] = []
        index = 0
        while index < len(self.source):
            char = self.source[index]
            if char.isspace():
                index += 1
                continue
            if char.isdigit() or char == ".":
                start = index
                dot_count = 0
                while index < len(self.source):
                    current = self.source[index]
                    if current == ".":
                        dot_count += 1
                        if dot_count > 1:
                            raise CalculationError(f"第 {index + 1} 位数字格式错误")
                    elif not current.isdigit():
                        break
                    index += 1
                value = self.source[start:index]
                if value == ".":
                    raise CalculationError(f"第 {start + 1} 位数字格式错误")
                tokens.append(Token("NUMBER", value, start))
                continue
            if char.isalpha():
                start = index
                while index < len(self.source) and self.source[index].isalpha():
                    index += 1
                tokens.append(Token("IDENTIFIER", self.source[start:index].lower(), start))
                continue
            if char in "+-*/%^()":
                kind = "PAREN" if char in "()" else "OPERATOR"
                tokens.append(Token(kind, char, index))
                index += 1
                continue
            raise CalculationError(f"第 {index + 1} 位包含不支持的字符“{char}”")

        tokens.append(Token("EOF", "", len(self.source)))
        return tokens


class ExpressionParser:
    """Parse and evaluate expressions using explicit grammar rules."""

    FUNCTIONS = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log10,
        "ln": math.log,
        "abs": abs,
    }
    CONSTANTS = {"pi": math.pi, "e": math.e}
    MAX_ABSOLUTE_RESULT = 1e100

    def __init__(self, expression: str) -> None:
        self.tokens = Tokenizer(expression).tokenize()
        self.position = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.position]

    def parse(self) -> float:
        result = self._expression()
        if self.current.kind != "EOF":
            raise CalculationError(f"第 {self.current.position + 1} 位附近存在多余内容")
        self._validate_result(result)
        return result

    def _expression(self) -> float:
        value = self._term()
        while self.current.value in {"+", "-"}:
            operator = self._advance().value
            right = self._term()
            value = value + right if operator == "+" else value - right
            self._validate_result(value)
        return value

    def _term(self) -> float:
        value = self._power()
        while self.current.value in {"*", "/", "%"}:
            operator = self._advance().value
            right = self._power()
            if operator in {"/", "%"} and right == 0:
                raise CalculationError("除数不能为零")
            if operator == "*":
                value *= right
            elif operator == "/":
                value /= right
            else:
                value %= right
            self._validate_result(value)
        return value

    def _power(self) -> float:
        value = self._unary()
        if self.current.value == "^":
            self._advance()
            exponent = self._power()
            try:
                value = math.pow(value, exponent)
            except (OverflowError, ValueError) as error:
                raise CalculationError("幂运算超出有效范围") from error
            self._validate_result(value)
        return value

    def _unary(self) -> float:
        if self.current.value in {"+", "-"}:
            operator = self._advance().value
            value = self._unary()
            return value if operator == "+" else -value
        return self._primary()

    def _primary(self) -> float:
        token = self.current
        if token.kind == "NUMBER":
            self._advance()
            return float(token.value)
        if token.value == "(":
            self._advance()
            value = self._expression()
            if self.current.value != ")":
                raise CalculationError("缺少右括号")
            self._advance()
            return value
        if token.kind == "IDENTIFIER":
            self._advance()
            if token.value in self.CONSTANTS:
                return self.CONSTANTS[token.value]
            function = self.FUNCTIONS.get(token.value)
            if function is None:
                raise CalculationError(f"不支持函数“{token.value}”")
            if self.current.value != "(":
                raise CalculationError(f"函数 {token.value} 后需要括号")
            self._advance()
            argument = self._expression()
            if self.current.value != ")":
                raise CalculationError("缺少右括号")
            self._advance()
            try:
                result = function(argument)
            except ValueError as error:
                raise CalculationError(f"函数 {token.value} 的参数无效") from error
            self._validate_result(result)
            return result
        if token.kind == "EOF":
            raise CalculationError("表达式不完整")
        raise CalculationError(f"第 {token.position + 1} 位附近语法错误")

    def _advance(self) -> Token:
        token = self.current
        self.position += 1
        return token

    def _validate_result(self, value: float) -> None:
        if not math.isfinite(value) or abs(value) > self.MAX_ABSOLUTE_RESULT:
            raise CalculationError("计算结果超出有效范围")


def calculate(expression: str) -> int | float:
    """Safely calculate an expression and normalize the JSON result."""

    result = ExpressionParser(expression).parse()
    if result == 0:
        return 0
    if result.is_integer() and abs(result) <= 9_007_199_254_740_991:
        return int(result)
    return float(f"{result:.12g}")
