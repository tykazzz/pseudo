"""
This module contains Lexer class using to tokenize stream.
"""

from pseudo.stream import Stream, EndOfFile
from pseudo.pseudo_types import String, Int, Operation, Statement, EOL, Variable,  Assignment, Bool

__author__ = u"Patryk Niedźwiedziński"


class Lexer():
    """
    Class to parse code.

    Attributes:
        i: A Stream instance with input code.
        keywords: A set of all keywords in pseudo.
        operators: A set of operators in pseudo.

    Usage:
    >>> lex = Lexer("pisz 12")
    >>> lex.read_next()
    Expression("pisz", args=[Number(12)])
    """

    def __init__(self, inp):
        """Inits Lexer with input."""
        self.i = Stream(inp)
        self.keywords = {"pisz", "koniec", "czytaj"}
        self.operators = {"+", "-", ":", "<"}

    def is_keyword(self, string) -> bool:
        """Checks if given string is a keyword."""
        return string in self.keywords

    def is_alphabet(self, c) -> bool:
        """Checks if given char is from alphabet."""
        ascii = ord(c)
        return (ascii >= 65 and ascii <= 90) or (ascii >= 97 and ascii <= 122)

    def is_digit(self, c) -> bool:
        """Checks if given char is a digit."""
        try:
            return ord(c) >= 48 and ord(c) <= 57
        except TypeError:
            return False

    def is_operator(self, c) -> bool:
        """Checks if given char is an allowed operator."""
        return c in self.operators

    def is_not_keyword_end(self, c) -> bool:
        """
        Checks if given char breaks parsing a keyword.

        Example:
        `asd1` - This is one keyword.
        `asd1+asd2` - This is two keywords with `+` in between them.
        """
        return c != " " and not self.is_operator(c)

    def read(self, test, eol=True) -> str:
        """
        Read an element of code from the stream based on given test function.

        Args:
            test: Function used to determine if next char should be included
                to expression.
            eol: Optional variable, which switches `end of line` to be included
                to expression.
        """

        expression = ""
        while not self.i.eof() and test(self.i.peek()):
            if eol and self.i.eol():
                break
            expression += self.i.next()
        return expression

    def read_number(self) -> Int:
        """Read a number from the stream."""
        number = self.read(self.is_digit)
        return Int(number)

    def read_string(self) -> String:
        """Read a string from the stream."""
        self.i.next()
        string = self.read(lambda c: c != "\"")
        self.i.next()
        return String(string)

    def read_keyword(self) -> str:
        """Read a keyword from the stream."""
        keyword = self.read(self.is_not_keyword_end)
        return keyword

    def read_args(self):
        """Read arguments from the stream."""
        arg = None
        prev_arg = None
        while True:
            arg = self.read_next(prev=prev_arg)
            if isinstance(arg, EOL):
                arg = prev_arg
                break
            prev_arg = arg
        return arg

    def read_next(self, prev=None):
        """Read next element from the stream and guess the type."""
        if self.i.eof():
            raise EndOfFile
        self.read(lambda c: c == "\n" or c == " ", eol=False)
        c = self.i.peek()
        if isinstance(c, EOL):
            self.i.next_line()
            if self.i.eof():
                raise EndOfFile
            return c
        if c == "#":
            self.i.next_line()
            return self.read_next()

        if c == "\"" or c == "\'":
            return self.read_string()

        if self.is_digit(c):
            return self.read_number()

        if self.is_operator(c):
            self.i.next()
            if (c == ":" and self.i.peek() == "=") or (c == "<" and self.i.peek() == "-"):
                self.i.next()
                return ":="
            return Operation(c, prev, self.read_next())

        if self.is_alphabet(c):
            col = self.i.col
            keyword = self.read_keyword()
            if self.is_keyword(keyword):
                arg = self.read_args()
                if keyword == "czytaj":
                    if not isinstance(arg, Variable):
                        self.i.throw("Statement 'czytaj' requires variable as argument")
                return Statement(keyword, args=arg)
            if keyword == "prawda":
                return Bool(1)
            if keyword == "fałsz":
                return Bool(0)
            if col == 1:
                operator = self.read_next()
                if operator != ":=":
                    self.i.throw(f"Invalid syntax")
                args = self.read_args()
                if not isinstance(args, Int) and not isinstance(args, String) and not isinstance(args, Operation):
                    self.i.throw(f"Cannot assign type {type(args)} to variable")
                return Assignment(Variable(keyword), args)
            return Variable(keyword)

        self.i.throw(f"Invalid character: '{c}'")
