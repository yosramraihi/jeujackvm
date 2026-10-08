import re
import sys

import Reader

"""Analyseur lexical Jack, conforme au cours."""


class Lexer:
    """Analyseur lexical Jack"""

    def __init__(self, file):
        self.reader = Reader.Reader(file)
        # position initiale pour les messages d'erreur
        self.line = self.reader._line
        self.col = self.reader._col
        self.tokens = [self._read(), self._read()]

    def _comment(self):
        """Gère les commentaires // et /* ... */ et renvoie None
        si c'était bien un commentaire, ou '/' si ce n'en était pas un.
        """
        # On consomme le '/' initial
        self.reader.next()
        # On regarde le caractère suivant SANS le consommer
        t = self.reader.look()
        if t is None:
            return '/'

        match t['char']:
            # Commentaire de ligne : // ... \n
            case '/':
                self.reader.next()  # consommer le second '/'
                t = self.reader.look()
                while t is not None and t['char'] != '\n':
                    self.reader.next()
                    t = self.reader.look()
                return None
            # Commentaire multilignes : /* ... */
            case '*':
                self.reader.next()  # consommer le '*'
                while True:
                    t = self.reader.look()
                    while t is not None and t['char'] != '*':
                        self.reader.next()
                        t = self.reader.look()
                    if t is None:
                        return None
                    self.reader.next()  # consommer '*'
                    t = self.reader.look()
                    if t is None:
                        return None
                    if t['char'] == '/':
                        self.reader.next()  # consommer '/'
                        return None
                    # sinon on continue la boucle
            # Ce n'était pas un commentaire, on retourne '/'
            case _:
                return '/'

    def _skip(self):
        """Passe au caractère suivant"""
        self.reader.next()
        return

    def _toke(self):
        """Lit un identifiant ou un entier (suite de [a-zA-Z0-9_])."""
        res = ''
        t = self.reader.look()
        while t is not None and re.fullmatch(r'[a-zA-Z0-9_]', t['char']):
            res += t['char']
            self.reader.next()
            t = self.reader.look()
        return res

    def _stringConstant(self):
        """Lit une constante chaîne de caractères"""
        res = ''
        # On a déjà consommé le '"' d'ouverture via _skip()
        t = self.reader.look()
        while t is not None and t['char'] != '"':
            res += t['char']
            self.reader.next()
            t = self.reader.look()
        # Consommer le '"' de fermeture
        if t is not None and t['char'] == '"':
            self.reader.next()
        return res

    def next(self):
        """Retourne le token courant et avance"""
        res = self.tokens[0]
        self.tokens[0] = self.tokens[1]
        self.tokens[1] = self._read()
        return res

    def _read(self):
        """Lit le prochain token"""
        token = None
        while self.reader.hasNext() and token is None:
            self.line = self.reader._line
            self.col = self.reader._col
            t = self.reader.look()
            if t is None:
                break
                
            char = t['char']
            # Utilise match/case pour classifier le caractère courant
            match char:
                case '/':
                    # Peut être un commentaire ou le symbole '/'
                    comment_result = self._comment()
                    if comment_result is not None:
                        token = "/"
                        # Ne pas faire _skip() car _comment() a déjà consommé le '/'
                # Symboles du langage Jack
                case '(' | ')' | '[' | ']' | '{' | '}' | ',' | ';' | '=' | '.' | '+' | '-' | '*' | '&' | '|' | '~' | '<' | '>':
                    token = char
                    self._skip()
                # Espaces blancs
                case ' ' | '\t' | '\n' | '\r':
                    self._skip()
                # Identifiants ou entiers
                case c if re.fullmatch(r'[a-zA-Z_]', c):
                    token = self._toke()
                # Entiers (commencent par un chiffre)
                case c if re.fullmatch(r'[0-9]', c):
                    token = self._toke()
                # Chaînes de caractères
                case '"':
                    self._skip()  # consommer le '"' d'ouverture
                    token = self._stringConstant()
                    # Le token est maintenant la chaîne sans les guillemets
                # Caractère invalide
                case _:
                    print(f'SyntaxError : caractère invalide "{char}" (line={self.line}, col={self.col})')
                    sys.exit(1)

        if token is None:
            return None
        else:
            pattern = self._pattern()
            group = pattern.fullmatch(token)
            if group is None:
                print(f'SyntaxError (line={self.line}, col={self.col}): token invalide "{token}"')
                sys.exit(1)
            else:
                # Déterminer le type du token
                token_type = group.lastgroup
                # Si c'est un identifiant, vérifier si c'est un mot-clé
                if token_type == 'identifier':
                    if token in self._keywords():
                        token_type = 'keyword'
                
                return {
                    'line': self.line, 
                    'col': self.col, 
                    'type': token_type, 
                    'token': token
                }

    def hasNext(self):
        """Vérifie s'il reste des tokens"""
        return self.tokens[0] is not None

    def look(self):
        """Retourne le token courant sans avancer"""
        return self.tokens[0]

    def look_ahead(self, n=1):
        """Retourne le token n positions après le courant"""
        if n == 0:
            return self.tokens[0]
        elif n == 1:
            return self.tokens[1]
        else:
            # Pour n > 1, on doit lire plus de tokens
            # Implémentation simplifiée pour l'instant
            return None

    def _pattern(self):
        """Pattern regex pour identifier les tokens"""
        return re.compile(r"""
            (?P<symbol>[()[\]{},;=.+\-*/&|~<>])|
            (?P<IntegerConstant>[0-9]+)|
            (?P<identifier>[a-zA-Z_][a-zA-Z0-9_]*)|
            (?P<StringConstant>.+)
        """, re.X)

    def _keywords(self):
        """Liste des mots-clés Jack"""
        return {
            'class', 'constructor', 'method', 'function', 'int', 'boolean', 
            'char', 'void', 'var', 'static', 'field', 'let', 'do', 'if', 
            'else', 'while', 'return', 'true', 'false', 'null', 'this'
        }

    def __iter__(self):
        return self

    def __next__(self):
        if self.hasNext():
            return self.next()
        else:
            raise StopIteration


if __name__ == "__main__":
    file = sys.argv[1]
    print('-----debut')
    lexer = Lexer(file)
    for token in lexer:
        print(token)
    print('-----fin')