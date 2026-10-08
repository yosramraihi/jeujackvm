import os
import glob
import sys
import Generator

class Translator:
    def __init__(self, files):
        self.files = files

    def translate(self):
        if os.path.isfile(self.files):
            self._translateonefile(self.files)
        elif os.path.isdir(self.files):
            for file in glob.glob(self.files + "/*.jack"):
                self._translateonefile(file)

    def _translateonefile(self, file):
        # Le Generator crée et écrit directement dans le fichier .vm
        gen = Generator.Generator(file)
        gen.jackclass()
        # Le fichier .vm est créé par le Generator dans le répertoire courant

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python Translator.py <jack file | dir>")
    else:
        t = Translator(sys.argv[1])
        t.translate()