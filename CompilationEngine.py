import JackTokenizer

class_var_dec = ['static', 'field']

vars = ['static', 'field', 'argument', 'var']

VAR = 'var'

ELSE = 'else'

ARG = 'argument'

unary_op_list = ['-', '~']

DOT = '.'

END_OF_LINE = ';'

OPEN_ROUND = '('

OPEN_SQUARE = '['

CLOSE_ROUND = ")"

COMMA = ','

CLOSE_TALTAL = '}'

OP = ['+', '-', '*', '/', '&', '|', '<', '>', '=']

op_dict = {'+': 'add', '-': 'sub', '*': 'call Math.multiply 2',
           '/': 'call Math.divide 2', '&': 'and', '|': 'or',
           '<': 'lt', '>': 'gt', '=': 'eq'}

unary_op_dict = {'-': 'neg', '~': 'not'}

CLASS_VAR_DEC = 'classVarDec'
VAR_DEC = 'varDec'


class CompilationEngine:
    """
    This module effects the actual compilation into XML form. It gets its
    input from a JackTokenizer and writes its parsed XML structure into an
    output file/stream. This is done by a series of compilexxx() methods,
    where xxx is a corresponding syntactic element of the Jack grammar. The
    contract between these methods is that each compilexxx() method should
    read the syntactic construct xxx from the input, advance() the tokenizer
    exactly beyond xxx, and output the XML parsing of xxx. Thus, compilexxx(
    )may only be called if indeed xxx is the next syntactic element of the
    input.
    """

    def __init__(self, input_file_path, output):
        """
        creates a new compilation engine with the given input and output.
        The next method called must be compileClass(). :param
        input_file_path: input file path :param output: output file to write
        to
        """
        self.tokenizer = JackTokenizer.JackTokenizer(input_file_path)
        self.file = output
        self.statements_func_dict = {'let': self.compile_let,
                                     'do': self.compile_do,
                                     'while': self.compile_while,
                                     'if': self.compile_if,
                                     'return': self.compile_return}
        self.scope = None
        self.while_counter = 0
        self.if_counter = 0
        self.buffer = []

    def write_class_to_file(self):
        """
        write all lines to file
        """
        for command in range(len(self.buffer) - 1):
            self.file.write(self.buffer[command])
            self.file.write('\n')
        self.file.write(self.buffer[-1])

    def remove_token(self):
        """
        advance the token by 1
        """
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()

    def compile_class(self):
        """
        compiles a complete class.
        """
        self.tokenizer.symbol_table.add_node()
        # <class>
        self.tokenizer.advance()
        # <keyword> class
        self.remove_token()
        # <identifier> class_name
        self.scope = self.tokenizer.get_curr_token()
        self.remove_token()
        # <symbol> {
        self.remove_token()
        # inner class
        while self.tokenizer.get_curr_token() != CLOSE_TALTAL:
            # classVarDec
            while self.tokenizer.key_word() in class_var_dec:
                self.compile_class_var_dec()
            # subroutine
            while self.tokenizer.token_type() is JackTokenizer.TokenType.KEYWORD:
                self.buffer += self.compile_subroutine()
        # <symbol> }
        self.remove_token()

        self.tokenizer.symbol_table.del_node()
        self.scope = None

    def compile_class_var_dec(self):
        """
        compiles a static declaration or a field declaration.
        :return: counter of how many vars appeared in line
        """
        return self.compile_var(CLASS_VAR_DEC)

    def compile_subroutine(self):
        """
        compiles a complete method, function, or constructor.
        :return: list of relevant VM code lines
        """

        lines = []

        num_of_fields = self.tokenizer.symbol_table.head_val.scope_counter[1]

        self.tokenizer.symbol_table.add_node()

        # <subroutineDec>
        # <keyword> constructor | function | method
        subroutine_type = self.tokenizer.get_curr_token()
        self.remove_token()
        # <keyword | identifier> type
        self.tokenizer.symbol_table.update_scope_return_type(
            self.tokenizer.get_curr_token())
        self.remove_token()
        # <identifier> subroutine name
        subroutine = self.tokenizer.get_curr_token()
        self.remove_token()
        # <symbol> (
        self.remove_token()
        lines += self.compile_parameter_list(subroutine_type)
        # <symbol> )
        self.remove_token()
        # <subroutineBody>
        # <symbol> {
        self.remove_token()
        var_dec_counter = 0
        while self.tokenizer.key_word() == VAR:
            var_dec_counter += self.compile_var_dec()
        lines.append('function ' + self.scope + '.' + subroutine + ' ' + str(
            var_dec_counter))
        if subroutine_type == 'method':
            lines.append('push argument 0')
            lines.append('pop pointer 0')
        elif subroutine_type == 'constructor':
            lines.append('push constant ' + str(num_of_fields))
            lines.append('call Memory.alloc 1')
            lines.append('pop pointer 0')
        lines += self.compile_statements()
        # <symbol> }
        self.remove_token()

        self.tokenizer.symbol_table.del_node()

        return lines

    def compile_parameter_list(self, subroutine_type):
        """
        compiles a (possibly empty) parameter list, not including the
        enclosing Parenthesis.
        :return: list of empty VM code lines
        """
        # <parameterList>
        if subroutine_type == 'method':
            self.tokenizer.symbol_table.head_val.scope_counter[2] += 1
        while self.tokenizer.get_curr_token() != CLOSE_ROUND:
            if self.tokenizer.get_curr_token() == COMMA:
                self.remove_token()
            symbol_type = self.tokenizer.get_curr_token()
            self.remove_token()
            # add_to_symbol_list
            self.tokenizer.symbol_table.head_val.var_dict[
                self.tokenizer.get_curr_token()] = (
                ARG, symbol_type,
                self.tokenizer.symbol_table.head_val.scope_counter[2])
            self.tokenizer.symbol_table.head_val.scope_counter[2] += 1
            self.remove_token()

        return []

    def compile_var_dec(self):
        """
        compiles a var declaration.
        :return: counter of how many vars appeared in line
        """
        return self.compile_var(VAR_DEC)

    def compile_var(self, element):
        """
        compile var
        :param element: element type - class var or var dec
        :return: counter of how many vars appeared in line
        """
        # docing is for classVarDec
        # <classVarDec>
        # <keyword> field | static

        var_counter = 1

        symbol_kind = self.tokenizer.get_curr_token()

        symbol_counter = self.tokenizer.symbol_table.head_val.scope_counter[
            vars.index(symbol_kind)]
        self.tokenizer.symbol_table.head_val.scope_counter[
            vars.index(symbol_kind)] += 1

        self.remove_token()
        # <keyword> type

        symbol_type = self.tokenizer.get_curr_token()

        self.remove_token()
        # <identifier>

        # add_to_symbol_list
        self.tokenizer.symbol_table.head_val.var_dict[
            self.tokenizer.get_curr_token()] = (
            symbol_kind, symbol_type, symbol_counter)

        self.remove_token()
        # , varName
        while self.tokenizer.get_curr_token() == COMMA:
            var_counter += 1
            self.remove_token()
            symbol_counter = \
                self.tokenizer.symbol_table.head_val.scope_counter[
                    vars.index(symbol_kind)]
            self.tokenizer.symbol_table.head_val.scope_counter[
                vars.index(symbol_kind)] += 1
            self.tokenizer.symbol_table.head_val.var_dict[
                self.tokenizer.get_curr_token()] = (
                symbol_kind, symbol_type, symbol_counter)
            self.remove_token()
        # <symbol> ;
        self.remove_token()

        return var_counter

    def compile_statements(self):
        """
        compiles a sequence of statements, not including the enclosing
        Parenthesis.
        :return: list of relevant VM code lines
        """
        lines = []
        while self.tokenizer.get_curr_token() != CLOSE_TALTAL:
            lines += self.statements_func_dict[
                self.tokenizer.get_curr_token()]()
        return lines

    def compile_let(self):
        """
        Compiles a let statement
        :return: list of relevant VM code lines
        """
        lines = []
        # let
        self.remove_token()
        var_name = self.tokenizer.get_curr_token()
        # varName
        self.remove_token()
        array_index = None
        if self.tokenizer.get_curr_token() == OPEN_SQUARE:
            array_index = self.pre_expression_compile()
        # =
        self.remove_token()
        to_assign = self.compile_expression()
        # ;
        self.remove_token()
        if array_index is not None:
            lines += array_index
            lines.append(
                'push ' + self.tokenizer.get_symbol_record(var_name)[0] + ' ' +
                str(self.tokenizer.get_symbol_record(var_name)[2]))
            lines.append('add')
            lines += to_assign
            lines.append('pop temp 0')
            lines.append('pop pointer 1')
            lines.append('push temp 0')
            lines.append('pop that 0')
        else:
            lines += to_assign
            lines.append(
                'pop ' + self.tokenizer.get_symbol_record(var_name)[0] + ' ' +
                str(self.tokenizer.get_symbol_record(var_name)[2]))
        return lines

    def pre_expression_compile(self):
        """
        compiles an expression including the Parenthesis
        :return: list of relevant VM code lines
        """
        # [ / (
        self.remove_token()
        to_return = self.compile_expression()
        # ] / )
        self.remove_token()
        return to_return

    def compile_subroutine_call(self, is_do):
        """
        compile subroutine call
        :param is_do: is called from do or let
        :return: list of relevant VM code lines
        """
        lines = []
        # subroutineName | var
        subroutine = self.tokenizer.get_curr_token()
        self.remove_token()
        if self.tokenizer.get_curr_token() == OPEN_ROUND:
            parameters, expression_counter = self.pre_compile_expression_list(
                True)
            subroutine = self.scope + '.' + subroutine
        else:
            var_name = subroutine
            # .
            self.remove_token()
            # subroutineName
            subroutine = self.tokenizer.get_curr_token()
            self.remove_token()
            var = self.tokenizer.get_symbol_record(var_name)
            parameters, expression_counter = self.pre_compile_expression_list(
                False)
            if var:
                expression_counter += 1
                lines.append('push ' + var[0] + ' ' +
                             str(var[2]))
                var_name = var[1]
            subroutine = var_name + '.' + subroutine
        lines += parameters
        lines.append('call ' + subroutine + ' ' + str(expression_counter))
        if is_do:
            lines.append('pop temp 0')
        return lines

    def compile_do(self):
        """
        Compiles a do statement
        :return: list of relevant VM code lines
        """
        lines = []
        # do
        self.remove_token()
        lines += self.compile_subroutine_call(True)
        # ;
        self.remove_token()
        return lines

    def pre_compile_expression_list(self, is_method):
        """
        compiles an expression list including the Parenthesis
        :return: list of relevant VM code lines, how many expressions
        """
        # (
        self.remove_token()
        to_return = self.compile_expression_list(is_method)
        # )
        self.remove_token()
        return to_return

    def compile_while(self):
        """
        Compiles a while statement
        :return: list of relevant VM code lines
        """
        while_num = self.while_counter
        self.while_counter += 1
        lines = ['label WHILE_EXP_' + str(while_num)]
        # while
        self.remove_token()
        lines += self.pre_expression_compile()
        lines.append('if-goto WHILE_BODY_' + str(while_num))
        lines.append('goto WHILE_END_' + str(while_num))
        lines.append('label WHILE_BODY_' + str(while_num))
        lines += self.pre_statements_compile()
        lines.append('goto WHILE_EXP_' + str(while_num))
        lines.append('label WHILE_END_' + str(while_num))
        return lines

    def pre_statements_compile(self):
        """
        compiles statements including the Parenthesis
        :return: list of relevant VM code lines
        """
        # {
        self.remove_token()
        to_return = self.compile_statements()
        # }
        self.remove_token()
        return to_return

    def compile_if(self):
        """
        compiles an if statement, possibly with a trailing else clause.
        :return: list of relevant VM code lines
        """
        lines = []
        if_num = self.if_counter
        self.if_counter += 1
        self.remove_token()
        lines += self.pre_expression_compile()
        lines.append('if-goto IF_START_' + str(if_num))
        if_statements = self.pre_statements_compile()
        else_statements = None
        if self.tokenizer.get_curr_token() == ELSE:
            self.remove_token()
            else_statements = self.pre_statements_compile()
        if else_statements:
            lines += else_statements
        lines.append('goto IF_END_' + str(if_num))
        lines.append('label IF_START_' + str(if_num))
        lines += if_statements
        lines.append('label IF_END_' + str(if_num))
        return lines

    def compile_return(self):
        """
        compiles a return statement.
        :return: list of relevant VM code lines
        """
        lines = []
        self.remove_token()
        if self.tokenizer.get_curr_token() != END_OF_LINE:
            lines += self.compile_expression()
        # ;
        self.remove_token()
        if self.tokenizer.symbol_table.get_scope_return_type() == 'void':
            lines.append('push constant 0')
        lines.append('return')
        return lines

    def compile_op(self):
        """
        :return: relevant command for current op token
        """
        op = self.tokenizer.get_curr_token()
        return op_dict[op]

    def compile_expression(self):
        """
        compiles an expression.
        :return: list of relevant VM code lines
        """
        lines = []
        term_lines = []
        term_lines += self.compile_term()
        add_term_lines = True
        while self.tokenizer.get_curr_token() in OP:
            add_term_lines = False
            # op
            op_line = self.compile_op()
            self.remove_token()
            term_lines += self.compile_term()
            lines += term_lines
            term_lines = []
            lines.append(op_line)
        if add_term_lines:
            lines += term_lines
        return lines

    def compile_term(self):
        """
        compiles a term. This method is faced with a slight difficulty when
        trying to decide between some of the alternative rules.
        Specifically, if the current token is an identifier, it must still
        distinguish between a variable, an array entry, and a subroutine
        call. The distinction can be made by looking ahead one extra token.
        :return: list of relevant VM code lines
        """
        lines = []
        const = self.tokenizer.get_curr_token()
        future_token = self.tokenizer.future_token()
        if const == OPEN_ROUND:
            lines += self.pre_expression_compile()
        elif const in unary_op_list:
            # unaryOp
            unary_op = unary_op_dict[self.tokenizer.get_curr_token()]
            self.remove_token()
            term = self.compile_term()
            lines += term
            lines.append(unary_op)
        elif self.tokenizer.token_type() is JackTokenizer.TokenType.IDENTIFIER:
            if future_token == OPEN_SQUARE:
                var_name = self.tokenizer.get_curr_token()
                self.remove_token()
                array_index = self.pre_expression_compile()
                lines += array_index
                lines.append(
                    'push ' + self.tokenizer.get_symbol_record(var_name)[
                        0] + ' ' +
                    str(self.tokenizer.get_symbol_record(var_name)[2]))
                lines.append('add')
                lines.append('pop pointer 1')
                lines.append('push that 0')
            elif future_token in [DOT, OPEN_ROUND]:
                lines += self.compile_subroutine_call(False)
            else:
                symbol_record = self.tokenizer.get_symbol_record(const)
                lines.append('push ' + symbol_record[0] + ' ' +
                             str(symbol_record[2]))
                self.remove_token()
        else:
            if const in ['null', 'false', 'true']:
                lines.append('push constant 0')
                if const == 'true':
                    lines.append('not')
            elif const == 'this':
                lines.append('push pointer 0')
            else:
                try:
                    lines.append('push constant ' + str(int(const)))
                except ValueError:
                    const = const[1:-1]
                    lines.append('push constant ' + str(len(const)))
                    lines.append('call String.new 1')
                    for letter in const:
                        char = ord(letter)
                        lines.append('push constant ' + str(char))
                        lines.append('call String.appendChar 2')
            self.remove_token()

        return lines

    def compile_expression_list(self, is_method):
        """
        compiles a (possibly empty) comma separated list of expressions.
        :return: list of relevant VM code lines, how many expressions
        """
        lines = []
        expression_counter = 0
        if is_method:
            lines.append('push pointer 0')
            expression_counter += 1
        while self.tokenizer.get_curr_token() != CLOSE_ROUND:
            if self.tokenizer.get_curr_token() == COMMA:
                self.remove_token()
            lines += self.compile_expression()
            expression_counter += 1
        return lines, expression_counter
