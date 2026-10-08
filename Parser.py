import sys
import Lexer


class Parser:
    """Analyseur syntaxique Jack complet, conforme à la grammaire du cours."""

    def __init__(self, file):
        self.lexer = Lexer.Lexer(file)

    # utilitaires -----------------------------
    def _peek(self):
        return self.lexer.look()

    def _eat(self, expected: str):
        tok = self.lexer.next()
        if tok is None or tok['token'] != expected:
            self._error(tok, expected)
        return tok

    def _error(self, tok, expected=""):
        if tok is None:
            print("Syntax error: end of file", ("; expected " + expected) if expected else "")
        else:
            print(f"SyntaxError (line={tok['line']}, col={tok['col']}): got {tok['token']}, expected {expected}")
        sys.exit(1)

    # grammaire -------------------------------
    def jackclass(self):
        """class: 'class' className '{' classVarDec* subroutineDec* '}'"""
        self._eat('class')
        name_tok = self.lexer.next()  # className
        classname = name_tok['token']
        self._eat('{')

        varDec = []
        while self._peek() and self._peek()['token'] in ('static', 'field'):
            varDec.extend(self.classVarDec())

        subroutines = []
        while self._peek() and self._peek()['token'] in ('constructor', 'function', 'method'):
            subroutines.append(self.subroutineDec())

        self._eat('}')
        return {
            'type': 'class',
            'name': classname,
            'varDec': varDec,
            'subroutine': subroutines,
        }

    def classVarDec(self):
        """classVarDec: ('static'| 'field') type varName (',' varName)* ';'"""
        kind_tok = self.lexer.next()  # static | field
        kind = kind_tok['token']
        type_tok = self.lexer.next()  # int | char | boolean | className
        vtype = type_tok['token']
        
        # Premier varName
        name_tok = self.lexer.next()  # varName
        names = [{'line': name_tok['line'], 'col': name_tok['col'], 'name': name_tok['token'], 'kind': kind, 'type': vtype}]
        
        # (',' varName)*
        while self._peek() and self._peek()['token'] == ',':
            self._eat(',')
            name_tok = self.lexer.next()  # varName
            names.append({'line': name_tok['line'], 'col': name_tok['col'], 'name': name_tok['token'], 'kind': kind, 'type': vtype})
        
        self._eat(';')
        return names

    def subroutineDec(self):
        """subroutineDec: ('constructor'| 'function'|'method') ('void'|type)
        subroutineName '(' parameterList ')' subroutineBody
        """
        stype_tok = self.lexer.next()   # constructor|function|method
        stype = stype_tok['token']
        ret_tok = self.lexer.next()     # void|type
        rtype = ret_tok['token']
        name_tok = self.lexer.next()    # subroutineName
        name = name_tok['token']
        self._eat('(')
        parameters = self.parameterList()
        self._eat(')')
        body = self.subroutineBody()
        return {
            'line': stype_tok['line'],
            'col': stype_tok['col'],
            'type': stype,
            'return': rtype,
            'name': name,
            'argument': parameters,
            'local': body['local'],
            'instructions': body['instructions'],
        }

    def parameterList(self):
        """parameterList: ((type varName) (',' type varName)*)?"""
        parameters = []
        if self._peek() and self._peek()['token'] != ')':
            type_tok = self.lexer.next()  # type
            vtype = type_tok['token']
            name_tok = self.lexer.next()  # varName
            parameters.append({
                'line': name_tok['line'],
                'col': name_tok['col'],
                'name': name_tok['token'],
                'kind': 'argument',
                'type': vtype
            })
            
            while self._peek() and self._peek()['token'] == ',':
                self._eat(',')
                type_tok = self.lexer.next()  # type
                vtype = type_tok['token']
                name_tok = self.lexer.next()  # varName
                parameters.append({
                    'line': name_tok['line'],
                    'col': name_tok['col'],
                    'name': name_tok['token'],
                    'kind': 'argument',
                    'type': vtype
                })
        
        return parameters

    def subroutineBody(self):
        """subroutineBody: '{' varDec* statements '}'"""
        self._eat('{')
        local = []
        while self._peek() and self._peek()['token'] == 'var':
            local.extend(self.varDec())
        instructions = self.statements()
        self._eat('}')
        return {'local': local, 'instructions': instructions}

    def varDec(self):
        """varDec: 'var' type varName (',' varName)* ';'"""
        var_tok = self.lexer.next()     # 'var'
        type_tok = self.lexer.next()
        vtype = type_tok['token']
        name_tok = self.lexer.next()
        name = name_tok['token']
        
        names = [{'line': name_tok['line'], 'col': name_tok['col'], 'name': name, 'kind': 'local', 'type': vtype}]
        
        # (',' varName)*
        while self._peek() and self._peek()['token'] == ',':
            self._eat(',')
            name_tok = self.lexer.next()  # varName
            names.append({
                'line': name_tok['line'],
                'col': name_tok['col'],
                'name': name_tok['token'],
                'kind': 'local',
                'type': vtype
            })
        
        self._eat(';')
        return names

    def statements(self):
        """statements : statement*"""
        res = []
        while self._peek() and self._peek()['token'] in ('let', 'return', 'if', 'while', 'do'):
            tok = self._peek()['token']
            if tok == 'let':
                res.append(self.letStatement())
            elif tok == 'return':
                res.append(self.returnStatement())
            elif tok == 'if':
                res.append(self.ifStatement())
            elif tok == 'while':
                res.append(self.whileStatement())
            elif tok == 'do':
                res.append(self.doStatement())
        return res

    def letStatement(self):
        """letStatement : 'let' varName ('[' expression ']')? '=' expression ';'"""
        let_tok = self.lexer.next()  # 'let'
        name_tok = self.lexer.next()  # varName
        name = name_tok['token']
        
        # Gestion des tableaux : ('[' expression ']')?
        indice = None
        if self._peek() and self._peek()['token'] == '[':
            self._eat('[')
            indice = self.expression()
            self._eat(']')
        
        self._eat('=')
        expr = self.expression()
        self._eat(';')
        return {
            'line': let_tok['line'],
            'col': let_tok['col'],
            'type': 'let',
            'variable': name,
            'indice': indice,
            'valeur': expr,
        }

    def ifStatement(self):
        """ifStatement : 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?"""
        if_tok = self.lexer.next()  # 'if'
        self._eat('(')
        condition = self.expression()
        self._eat(')')
        self._eat('{')
        true_block = self.statements()
        self._eat('}')

        false_block = []
        if self._peek() and self._peek()['token'] == 'else':
            self.lexer.next()  # 'else'
            self._eat('{')
            false_block = self.statements()
            self._eat('}')

        return {
            'line': if_tok['line'],
            'col': if_tok['col'],
            'type': 'if',
            'condition': condition,
            'true': true_block,
            'false': false_block,
        }

    def whileStatement(self):
        """whileStatement : 'while' '(' expression ')' '{' statements '}'"""
        while_tok = self.lexer.next()  # 'while'
        self._eat('(')
        condition = self.expression()
        self._eat(')')
        self._eat('{')
        body = self.statements()
        self._eat('}')
        return {
            'line': while_tok['line'],
            'col': while_tok['col'],
            'type': 'while',
            'condition': condition,
            'instructions': body,
        }

    def doStatement(self):
        """doStatement : 'do' subroutineCall ';'"""
        do_tok = self.lexer.next()  # 'do'
        call = self.subroutineCall()
        self._eat(';')
        
        return {
            'line': do_tok['line'],
            'col': do_tok['col'],
            'type': 'do',
            'classvar': call['classvar'],
            'name': call['name'],
            'argument': call['argument'],
        }

    def returnStatement(self):
        """returnStatement : 'return' expression? ';'"""
        ret_tok = self.lexer.next()  # 'return'
        if self._peek() and self._peek()['token'] != ';':
            expr = self.expression()
        else:
            expr = None
        self._eat(';')
        return {'line': ret_tok['line'], 'col': ret_tok['col'], 'type': 'return', 'valeur': expr}

    def expression(self):
        """expression : term (op term)*"""
        items = []
        # premier term obligatoire
        items.append(self.term())
        # boucle sur (op term)*
        while self._peek() and self._peek()['token'] in ('+','-','*','/','&','|','<','>','='):
            op_tok = self.lexer.next()
            items.append(op_tok['token'])  # on garde juste le symbole de l'opérateur
            items.append(self.term())
        return items

    def term(self):
        """term : integerConstant | stringConstant | keywordConstant 
                | varName | varName '[' expression ']' | subroutineCall 
                | '(' expression ')' | unaryOp term
        """
        tok = self._peek()

        # parenthèses : '(' expression ')'
        if tok and tok['token'] == '(':
            self._eat('(')
            expr = self.expression()
            self._eat(')')
            return {
                'line': tok['line'],
                'col': tok['col'],
                'type': 'paren',
                'value': expr,
            }

        # opérateurs unaires '-' ou '~'
        if tok and tok['token'] in ('-', '~'):
            op_tok = self.lexer.next()
            sub_term = self.term()
            return {
                'line': op_tok['line'],
                'col': op_tok['col'],
                'type': 'unary',
                'op': op_tok['token'],
                'term': sub_term,
            }

        # stringConstant
        if tok and tok['type'] == 'StringConstant':
            str_tok = self.lexer.next()
            return {
                'line': str_tok['line'],
                'col': str_tok['col'],
                'type': 'string',
                'value': str_tok['token'],
            }

        # keywordConstant : true, false, null, this
        if tok and tok['token'] in ('true', 'false', 'null', 'this'):
            kw_tok = self.lexer.next()
            return {
                'line': kw_tok['line'],
                'col': kw_tok['col'],
                'type': 'constant',
                'value': kw_tok['token'],
            }

        # subroutineCall
        if tok and tok['type'] == 'identifier':
            next_tok = self.lexer.look_ahead(1)
            if next_tok and next_tok['token'] in ('(', '.'):
                call = self.subroutineCall()
                return {
                    'line': tok['line'],
                    'col': tok['col'],
                    'type': 'call',
                    'subroutineCall': call,
                }

        # varName avec ou sans indice
        if tok and tok['type'] == 'identifier':
            name_tok = self.lexer.next()
            
            # Vérifier si c'est un accès à un tableau : varName '[' expression ']'
            if self._peek() and self._peek()['token'] == '[':
                self._eat('[')
                indice = self.expression()
                self._eat(']')
                return {
                    'line': name_tok['line'],
                    'col': name_tok['col'],
                    'type': 'varName',
                    'value': name_tok['token'],
                    'indice': indice,
                }
            else:
                # Simple variable
                return {
                    'line': name_tok['line'],
                    'col': name_tok['col'],
                    'type': 'varName',
                    'value': name_tok['token'],
                    'indice': None,
                }

        # integerConstant
        if tok and tok['type'] == 'IntegerConstant':
            int_tok = self.lexer.next()
            return {
                'line': int_tok['line'],
                'col': int_tok['col'],
                'type': 'int',
                'value': int(int_tok['token']),
            }

        self._error(tok, "term")

    def subroutineCall(self):
        """subroutineCall: subroutineName '(' expressionList ')' 
                        | (className | varName) '.' subroutineName '(' expressionList ')'
        """
        first_tok = self.lexer.next()  # subroutineName ou className/varName
        first_name = first_tok['token']
        
        # Deuxième cas : className '.' subroutineName
        if self._peek() and self._peek()['token'] == '.':
            self._eat('.')
            sub_name_tok = self.lexer.next()  # subroutineName
            class_name = first_name
            sub_name = sub_name_tok['token']
        else:
            # Premier cas : subroutineName seul
            class_name = None
            sub_name = first_name
        
        self._eat('(')
        args = self.expressionList()
        self._eat(')')
        
        return {
            'classvar': class_name,
            'name': sub_name,
            'argument': args,
        }

    def expressionList(self):
        """expressionList: (expression (',' expression)*)?"""
        expressions = []
        if self._peek() and self._peek()['token'] != ')':
            expressions.append(self.expression())
            while self._peek() and self._peek()['token'] == ',':
                self._eat(',')
                expressions.append(self.expression())
        return expressions


if __name__ == "__main__":
    file = sys.argv[1]
    print('-----debut')
    parser = Parser(file)
    arbre = parser.jackclass()
    print(arbre)
    print('-----fin')