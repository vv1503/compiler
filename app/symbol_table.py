from __future__ import annotations


class SymbolInfo:
    def __init__(self, name, kind, type_name, decl_line):
        self.name = name
        self.kind = kind
        self.type_name = type_name
        self.decl_line = decl_line


class SymbolTable:
    """Область видимости: объявления в текущей таблице; поиск с учётом родителя."""

    def __init__(self, parent=None):
        self.parent = parent
        self._syms = {}

    def declare(self, name, kind, type_name, decl_line):
        if name in self._syms:
            return False, self._syms[name].decl_line
        self._syms[name] = SymbolInfo(name, kind, type_name, decl_line)
        return True, None

    def lookup(self, name):
        if name in self._syms:
            return self._syms[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        return None
