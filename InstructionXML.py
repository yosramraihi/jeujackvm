"""InstructionXML

Ce module était une ébauche redondante avec ParserXML et contenait
de nombreuses erreurs de syntaxe et de conception.

Selon le cours fourni, l'analyse syntaxique doit être réalisée par
un parseur unique (Parser / ParserXML) et non par une seconde classe
InstructionXML séparée. Pour éviter des erreurs d'import et de
compilation, nous neutralisons ce fichier tout en le laissant
présent dans le projet.

Si besoin, vous pourrez ultérieurement réimplémenter ici des
fonctions utilitaires en vous basant sur la grammaire du cours.

"""


class InstructionXML:
    """Classe neutralisée : conservée uniquement pour compatibilité.

    Aucune logique n'est actuellement implémentée ici. L'analyse
    et la génération XML sont assurées par ParserXML.
    """

    def __init__(self, *args, **kwargs):
        # Accept any arguments for rétrocompatibilité mais ne rien faire.
        pass