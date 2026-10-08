"""Générateur Jack  VM complet avec gestion des classes, méthodes, constructeurs et variables."""

import sys
import Parser


class Generator:
    def __init__(self, file: str | None = None):
        if file is not None:
            self.parser = Parser.Parser(file)
            self.arbre = self.parser.jackclass()
            self.nameClass = self.arbre['name']
            self.vmfile = open(self.nameClass + '.vm', 'w')
            self.symbolClassTable = {}
            self.symbolRoutineTable = {}
            self.nbVarStatic = 0
            self.nbVarField = 0
            self.labelCounter = 0

    def jackclass(self):
        """Traite la classe entière et génère le code VM."""
        # Remplir la table des symboles de classe (static et field)
        for var in self.arbre['varDec']:
            self.addClassVariable(var)
        
        # Générer le code pour chaque sous-routine
        for routine in self.arbre['subroutine']:
            self.subroutine(routine)

    def addClassVariable(self, var):
        """Ajoute une variable de classe (static ou field) à la table des symboles."""
        info = {'type': var['type'], 'kind': var['kind']}
        if var['kind'] == 'static':
            info['index'] = self.nbVarStatic
            self.nbVarStatic += 1
        elif var['kind'] == 'field':
            info['index'] = self.nbVarField
            self.nbVarField += 1
        self.symbolClassTable[var['name']] = info

    def subroutine(self, routine):
        """Génère le code VM pour une sous-routine."""
        name = routine['name']
        routine_type = routine['type']
        full_name = f"{self.nameClass}.{name}"
        
        # Réinitialiser la table des symboles de routine
        self.symbolRoutineTable = {}
        self.nbVarArgument = 0
        self.nbVarLocal = 0

        # Pour les méthodes, ajouter 'this' comme premier argument
        if routine_type == 'method':
            self.symbolRoutineTable['this'] = {
                'type': self.nameClass, 
                'kind': 'argument', 
                'index': self.nbVarArgument
            }
            self.nbVarArgument += 1

        # Ajouter les arguments formels
        for arg in routine['argument']:
            self.symbolRoutineTable[arg['name']] = {
                'type': arg['type'],
                'kind': 'argument',
                'index': self.nbVarArgument
            }
            self.nbVarArgument += 1

        # Ajouter les variables locales
        for local in routine['local']:
            self.symbolRoutineTable[local['name']] = {
                'type': local['type'],
                'kind': 'local',
                'index': self.nbVarLocal
            }
            self.nbVarLocal += 1

        # Écrire l'en-tête de fonction
        self.vmfile.write(f"function {full_name} {self.nbVarLocal}\n")

        # Initialisation pour les méthodes et constructeurs
        if routine_type == 'method':
            # Pointer THIS vers l'objet courant
            self.vmfile.write("push argument 0\n")
            self.vmfile.write("pop pointer 0\n")
        elif routine_type == 'constructor':
            # Allouer de la mémoire pour l'objet
            self.vmfile.write(f"push constant {self.nbVarField}\n")
            self.vmfile.write("call Memory.alloc 1\n")
            self.vmfile.write("pop pointer 0\n")

        # Générer les instructions
        for inst in routine['instructions']:
            self.statement(inst)

    def statement(self, inst):
        """Dispatch sur le type d'instruction."""
        match inst['type']:
            case 'let':
                self.letStatement(inst)
            case 'return':
                self.returnStatement(inst)
            case 'if':
                self.ifStatement(inst)
            case 'while':
                self.whileStatement(inst)
            case 'do':
                self.doStatement(inst)
            case _:
                self.error(f"Instruction non supportée: {inst['type']}")

    def letStatement(self, inst):
        """Génère le code VM pour une affectation."""
        # Générer la valeur à assigner
        self.expression(inst['valeur'])
        
        var_name = inst['variable']
        info = self.lookupVariable(var_name)
        
        if info is None:
            self.error(f"Variable inconnue: {var_name}")

        # Gestion des tableaux
        if 'indice' in inst and inst['indice'] is not None:
            # Accès à un élément de tableau
            self.expression(inst['indice'])
            self.vmfile.write(f"push {info['kind']} {info['index']}\n")
            self.vmfile.write("add\n")
            self.vmfile.write("pop pointer 1\n")
            self.vmfile.write("pop that 0\n")
        else:
            # Affectation simple
            self.vmfile.write(f"pop {info['kind']} {info['index']}\n")

    def returnStatement(self, inst):
        """Génère le code VM pour return."""
        if inst['valeur'] is not None:
            self.expression(inst['valeur'])
        else:
            # Pour void functions, retourner 0
            self.vmfile.write("push constant 0\n")
        self.vmfile.write("return\n")

    def ifStatement(self, inst):
        """Génère le code VM pour un if (avec ou sans else)."""
        label_true = self.newLabel("IF_TRUE")
        label_false = self.newLabel("IF_FALSE")
        label_end = self.newLabel("IF_END")

        # Évaluer la condition
        self.expression(inst['condition'])
        
        # if-goto vrai
        self.vmfile.write(f"if-goto {label_true}\n")
        
        if inst['false']:
            # Avec else
            self.vmfile.write(f"goto {label_false}\n")
            self.vmfile.write(f"label {label_true}\n")
            for s in inst['true']:
                self.statement(s)
            self.vmfile.write(f"goto {label_end}\n")
            self.vmfile.write(f"label {label_false}\n")
            for s in inst['false']:
                self.statement(s)
            self.vmfile.write(f"label {label_end}\n")
        else:
            # Sans else
            self.vmfile.write(f"goto {label_end}\n")
            self.vmfile.write(f"label {label_true}\n")
            for s in inst['true']:
                self.statement(s)
            self.vmfile.write(f"label {label_end}\n")

    def whileStatement(self, inst):
        """Génère le code VM pour un while."""
        label_exp = self.newLabel("WHILE_EXP")
        label_end = self.newLabel("WHILE_END")

        self.vmfile.write(f"label {label_exp}\n")
        self.expression(inst['condition'])
        self.vmfile.write("not\n")
        self.vmfile.write(f"if-goto {label_end}\n")

        for s in inst['instructions']:
            self.statement(s)

        self.vmfile.write(f"goto {label_exp}\n")
        self.vmfile.write(f"label {label_end}\n")
        
    def doStatement(self, inst):
        """Génère le code VM pour do subroutineCall();"""
        self.subroutineCall(inst)
        # Ignorer la valeur de retour
        self.vmfile.write("pop temp 0\n")

    def expression(self, exp):
        """Génère le code VM pour une expression."""
        self.term(exp[0])
        i = 1
        while i < len(exp):
            op = exp[i]
            self.term(exp[i + 1])
            self.vmfile.write({
                '+': "add\n",
                '-': "sub\n",
                '*': "call Math.multiply 2\n",
                '/': "call Math.divide 2\n",
                '&': "and\n",
                '|': "or\n",
                '<': "lt\n",
                '>': "gt\n",
                '=': "eq\n",
            }[op])
            i += 2

    def term(self, t):
        """Génère le code VM pour un term."""
        match t['type']:
            case 'int':
                self.vmfile.write(f"push constant {t['value']}\n")
            case 'string':
                self.generateStringConstant(t['value'])
            case 'constant':
                self.generateKeywordConstant(t['value'])
            case 'varName':
                self.generateVariableAccess(t)
            case 'call':
                self.subroutineCall(t['subroutineCall'])
            case 'paren':
                self.expression(t['value'])
            case 'unary':
                self.term(t['term'])
                op = t['op']
                if op == '-':
                    self.vmfile.write("neg\n")
                elif op == '~':
                    self.vmfile.write("not\n")
            case _:
                self.error(f"Term non supporté: {t['type']}")

    def generateStringConstant(self, string_value):
        """Génère le code VM pour une constante string."""
        length = len(string_value)
        self.vmfile.write(f"push constant {length}\n")
        self.vmfile.write("call String.new 1\n")
        for char in string_value:
            self.vmfile.write(f"push constant {ord(char)}\n")
            self.vmfile.write("call String.appendChar 2\n")

    def generateKeywordConstant(self, keyword):
        """Génère le code VM pour true, false, null, this."""
        match keyword:
            case 'true':
                self.vmfile.write("push constant 0\n")
                self.vmfile.write("not\n")
            case 'false' | 'null':
                self.vmfile.write("push constant 0\n")
            case 'this':
                self.vmfile.write("push pointer 0\n")

    def generateVariableAccess(self, t):
        """Génère le code VM pour l'accès à une variable."""
        var_name = t['value']
        info = self.lookupVariable(var_name)
        
        if info is None:
            self.error(f"Variable non déclarée: {var_name}")

        # Gestion des tableaux
        if 'indice' in t and t['indice'] is not None:
            self.expression(t['indice'])
            self.vmfile.write(f"push {info['kind']} {info['index']}\n")
            self.vmfile.write("add\n")
            self.vmfile.write("pop pointer 1\n")
            self.vmfile.write("push that 0\n")
        else:
            self.vmfile.write(f"push {info['kind']} {info['index']}\n")

    def subroutineCall(self, call):
        """Génère le code VM pour un appel de sous-routine."""
        n_args = 0
        class_name = call.get('classvar')
        sub_name = call['name']
        args = call['argument']

        # Déterminer le nom complet de la fonction et préparer les arguments
        if class_name in self.symbolClassTable or class_name in self.symbolRoutineTable:
            # Appel de méthode sur un objet
            info = self.lookupVariable(class_name)
            if info is None:
                self.error(f"Variable non trouvée: {class_name}")
            
            # Empiler l'objet (this)
            self.vmfile.write(f"push {info['kind']} {info['index']}\n")
            n_args += 1
            
            # Nom complet de la méthode
            actual_class = info['type']
            full_name = f"{actual_class}.{sub_name}"
        else:
            # Appel de fonction ou constructeur
            if class_name is None:
                # Méthode sur l'objet courant
                self.vmfile.write("push pointer 0\n")
                n_args += 1
                full_name = f"{self.nameClass}.{sub_name}"
            else:
                # Fonction statique ou constructeur
                full_name = f"{class_name}.{sub_name}"

        # Empiler les arguments
        for arg in args:
            self.expression(arg)
            n_args += 1

        # Appel de la fonction
        self.vmfile.write(f"call {full_name} {n_args}\n")

    def lookupVariable(self, var_name):
        """Recherche une variable dans les tables des symboles."""
        if var_name in self.symbolRoutineTable:
            return self.symbolRoutineTable[var_name]
        elif var_name in self.symbolClassTable:
            info = self.symbolClassTable[var_name]
            # Convertir 'field' en 'this' pour l'accès VM
            if info['kind'] == 'field':
                return {'type': info['type'], 'kind': 'this', 'index': info['index']}
            return info
        return None

    def newLabel(self, prefix):
        """Génère un label unique."""
        self.labelCounter += 1
        return f"{prefix}_{self.labelCounter}"

    def error(self, message: str = ''):
        print(f"SyntaxError: {message}")
        sys.exit(1)


if __name__ == '__main__':
    file = sys.argv[1]
    print('-----debut')
    generator = Generator(file)
    generator.jackclass()
    print('-----fin')