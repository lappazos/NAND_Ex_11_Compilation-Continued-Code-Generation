import re
from enum import Enum

EMPTY_STRING = ''

SPACE = " "

keyword_list = ['class', 'constructor', 'function', 'method', 'field',
                'static',
                'var', 'int', 'char', 'boolean', 'void', 'true', 'false',
                'null', 'this',
                'let', 'do', 'if', 'else', 'while', 'return']

symbol_list = ['{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/',
               '&', '|', '<', '>', '=', '~']
symbol_dict = {'<': '&lt;', '>': '&gt;', '"': '&quot;', '&': '&amp;'}

ARG = 'argument'
VAR = 'var'

kind_to_segment_dict = {ARG: ARG, VAR: 'local', 'static': 'static',
                        'field': 'this'}


class Node:
    """
    Node for linked list, to hold data per scope
    """
    def __init__(self, var_dict=None):
        self.var_dict = var_dict
        self.scope_counter = [0, 0, 0, 0]  # [static,field] / [argument, var]
        self.scope_return_type = None
        self.next_val = None


class SLinkedList:
    """
    linked list to hold the variables per scope
    """
    def __init__(self):
        self.head_val = None

    def add_node(self):
        if self.head_val is None:
            self.head_val = Node({})
        else:
            new_scope = Node({})
            new_scope.next_val = self.head_val
            self.head_val = new_scope

    def del_node(self):
        self.head_val = self.head_val.next_val

    def update_scope_return_type(self, return_type):
        self.head_val.scope_return_type = return_type

    def get_scope_return_type(self):
        return self.head_val.scope_return_type


class TokenType(Enum):
    """
    Class of Enums that represent token type
    """
    KEYWORD = 1
    SYMBOL = 2
    IDENTIFIER = 3
    INT_CONST = 4
    STRING_CONST = 5


class JackTokenizer:
    """
    Handles the parsing of a single .vm file, and encapsulates access to the
    input code. It reads VM commands, parses them, and provides convenient
    access to their components. In addition, it removes all white space and
    comments.
    """

    def __init__(self, file_path):
        """
        Constructor - Opens the input file/stream and gets ready to parse it.
        :param file_path: Input file / stream
        """
        self.file = open(file_path, 'r')
        self._jack_code = self.file.readlines()
        self.file.close()
        self._jack_code = self.clean_lines(self._jack_code)
        self._curr_index = 0
        self._length = len(self._jack_code)
        self._curr_token = None

        self.symbol_table = SLinkedList()

    def has_more_tokens(self):
        """
        Are there more commands in the input?
        :return: boolean
        """
        return self._curr_index <= (self._length - 1)

    def advance(self):
        """
        Reads the next command from the input and makes it the current
        command. Should be called only if hasMoreCommands is true. Initially
        there is no current command.
        """
        self._curr_token = self._jack_code[self._curr_index]
        self._curr_index += 1

    def future_token(self):
        """
        :return: current +1 token
        """
        return self._jack_code[self._curr_index]

    def token_type(self):
        """
        Returns the type of the current VM command. C_ARITHMETIC is returned
        for all the arithmetic commands :return: C_ARITHMETIC, C_PUSH,
        C_POP, C_LABEL, C_GOTO, C_IF, C_FUNCTION, C_RETURN, C_CALL
        """
        if self._curr_token in symbol_list:
            return TokenType.SYMBOL
        elif self._curr_token in keyword_list:
            return TokenType.KEYWORD
        elif self._curr_token.startswith('"') and self._curr_token.endswith(
                '"'):
            return TokenType.STRING_CONST
        elif self._curr_token.isdigit():
            return TokenType.INT_CONST
        else:
            return TokenType.IDENTIFIER

    def key_word(self):
        """
        returns the keyword which is the current token. Should be called
        only when tokenType() is KEYWORD. :return: keyword stirng
        """
        return self._curr_token

    @staticmethod
    def clean_lines(file):
        """
        get an array of lines and clear the whitespaces and comments
        :param file: vm lines array
        :return: cleaned vm lines array
        """
        lines = []
        for line in file:
            if '//' in line:
                if line.count('"', 0, line.find('//')) % 2 == 0:
                    line = line[:line.find('//')]
            lines.append(line)
        one_string = EMPTY_STRING.join(lines)
        one_string = re.sub('\n', EMPTY_STRING, one_string)
        one_string = re.sub('/\*.*?\*/', EMPTY_STRING, one_string)
        string_split = one_string.split('"')
        tokens = []
        for i in range(len(string_split)):
            if i % 2 == 0:
                for symbol in symbol_list:
                    string_split[i] = string_split[i].replace(symbol,
                                                              SPACE + symbol + SPACE)
                string_split[i] = re.sub(r'\s+', SPACE, string_split[i])
                tokens = tokens + string_split[i].split()
            else:
                tokens = tokens + ['"' + string_split[i] + '"']
        return tokens

    def get_curr_token(self):
        return self._curr_token

    def get_symbol_record(self, var_name):
        """
        get the record of variable
        :param var_name: variable
        :return: symbol_kind, symbol_type, symbol_counter
        """
        temp_scope = self.symbol_table.head_val
        while temp_scope is not None:
            if var_name in temp_scope.var_dict:
                identifier_record = temp_scope.var_dict[var_name]
                return kind_to_segment_dict[identifier_record[0]], \
                       identifier_record[1], identifier_record[2]
            temp_scope = temp_scope.next_val
            if temp_scope is None:
                return None
