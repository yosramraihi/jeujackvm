"""No comment"""

import os
import sys


class Reader:
    """No comment"""

    def __init__(self, file):
        self.char = None
        self._line = 1
        self._col = 1
        if os.path.exists(file):
            self.file = open(file, "r")
            self.char = self.file.read(1)

    def look(self):
        """No comment"""
        if self.char:
            return {'line': self._line, 'col': self._col, 'char': self.char}
        return None

    def next(self):
        """No comment"""
        if self.char:
            res = {'line': self._line, 'col': self._col, 'char': self.char}
            if self.hasNext():
                if self.char == '\n':
                    self._line += 1
                    self._col = 1
                else:
                    self._col += 1
                self.char = self.file.read(1)
                if not self.hasNext():
                    self.file.close()
            else :
                self.char = None
            return res
        else :
            return None

    def hasNext(self):
        """No comment"""
        if self.char:
            return True
        else:
            return False

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
    lecteur = Reader(file)
    for c in lecteur:
        print(c)
    print('-----fin')
