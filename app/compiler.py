import sys
import os
import re

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QSplitter,
    QWidget,
    QVBoxLayout,
    QMenuBar,
    QMenu,
    QToolBar,
    QFileDialog,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QTextBrowser,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QStyle,
    QLabel,
    QComboBox,
    QPushButton,
    QGroupBox,
    QLineEdit,
)

from PyQt6.QtGui import (
    QIcon,
    QKeySequence,
    QAction,
    QFont,
    QTextCharFormat,
    QColor,
    QPainter,
    QTextFormat,
    QSyntaxHighlighter,
    QTextCursor,
    QBrush
)

from PyQt6.QtCore import Qt, QSize, QRect, QRegularExpression, QTimer
from translations import Translator
from lexical_analyzer import LexicalAnalyzer
from syntax_parser import SyntaxParser
from ast_nodes import ast_to_json, format_ast_tree
from ast_visual_view import AstGraphDialog


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        
        self.current_search_extra_selections = []  
        self.overwrite_mode = False
        
        font = QFont("Courier New", 10)
        self.setFont(font)
        
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width()
        self.highlight_current_line()

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 8 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def update_line_number_area_width(self):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def paint_line_numbers(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(240, 240, 240))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(120, 120, 120))
                painter.drawText(0, int(top), self.line_number_area.width() - 5,
                                 self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self):
        """Подсветка текущей строки"""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(230, 230, 255))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        if hasattr(self, 'current_search_extra_selections'):
            extra_selections.extend(self.current_search_extra_selections)
        
        self.setExtraSelections(extra_selections)

    def keyPressEvent(self, event):
        if self.overwrite_mode and not event.modifiers() and len(event.text()) > 0:
            cursor = self.textCursor()
            if not cursor.hasSelection() and not cursor.atBlockEnd():
                cursor.deleteChar()
        super().keyPressEvent(event)

    def clear_highlights(self):
        self.current_search_extra_selections = []
        self.highlight_current_line()

    def highlight_substring(self, start_line, start_col, length):
        """Подсвечивает подстроку в тексте"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        
        for _ in range(start_line - 1):
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        
        for _ in range(start_col - 1):
            cursor.movePosition(QTextCursor.MoveOperation.Right)
        
        highlight_cursor = self.textCursor()
        highlight_cursor.setPosition(cursor.position())
        highlight_cursor.movePosition(QTextCursor.MoveOperation.Right, 
                                     QTextCursor.MoveMode.KeepAnchor, length)
        
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QBrush(QColor(144, 238, 144)))  
        highlight_format.setForeground(QColor(0, 0, 0))
        
        extra = QTextEdit.ExtraSelection()
        extra.format = highlight_format
        extra.cursor = highlight_cursor
        
        self.current_search_extra_selections = [extra]
        self.highlight_current_line()
        
        self.setTextCursor(cursor)
        self.centerCursor()


class SimpleSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(86, 156, 214))  
        keyword_format.setFontWeight(QFont.Weight.Bold)

        keywords = ['var', 'const', 'if', 'else', 'while', 'for', 'return', 'true', 'false', 'int', 'float', 'string']
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor(206, 145, 120))  
        self.highlighting_rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(106, 153, 85))  
        self.highlighting_rules.append((QRegularExpression(r"//.*"), comment_format))
        self.highlighting_rules.append((QRegularExpression(r"/\*.*?\*/"), comment_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor(39, 107, 0))  
        self.highlighting_rules.append((QRegularExpression(r'\b\d+(?:\.\d+)?\b'), number_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class HelpWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent) 
        self.parent = parent
        self.setWindowTitle(self.parent.tr("Справка - Руководство пользователя - Compiler"))
        self.resize(1000, 600)

        layout = QHBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel(self.parent.tr("Разделы справки"))
        self.tree.setMinimumWidth(280)

        self.content = QTextBrowser()
        self.content.setOpenExternalLinks(True)

        layout.addWidget(self.tree, 1)
        layout.addWidget(self.content, 3)

        self.build_tree()
        self.tree.currentItemChanged.connect(self.show_content)
        self.tree.expandAll()

    def build_tree(self):
        tr = self.parent.tr

        general = QTreeWidgetItem([tr("Общая информация")])
        general.setData(0, Qt.ItemDataRole.UserRole, f"""
        <h2>{tr("Общая информация")}</h2>
        <p>{tr("Приложение содержит область редактирования текста, область вывода результатов анализа, главное меню, панель инструментов и строку состояния.")}</p>
        """)

        file_menu = QTreeWidgetItem([tr("Меню Файл")])

        create = QTreeWidgetItem([f"{tr('Создать')} (Ctrl+N)"])
        create.setData(0, Qt.ItemDataRole.UserRole, f"""
        <h2>{tr('Создать')}</h2>
        <p><b>{tr('Назначение')}:</b> {tr('Создание нового текстового документа.')}</p>
        <p><b>{tr('Функциональность')}:</b> {tr('Очищает область редактирования и сбрасывает имя текущего файла.')}</p>
        <p><b>{tr('Дополнительно')}:</b> {tr('При наличии несохранённых изменений пользователю предлагается сохранить данные.')}</p>
        """)

        open_ = QTreeWidgetItem([f"{tr('Открыть')} (Ctrl+O)"])
        open_.setData(0, Qt.ItemDataRole.UserRole, f"""
        <h2>{tr('Открыть')}</h2>
        <p><b>{tr('Назначение')}:</b> {tr('Загрузка текстового файла с диска.')}</p>
        <p><b>{tr('Поддерживаемый формат')}:</b> .txt</p>
        <p>{tr('После открытия содержимое файла отображается в области редактирования.')}</p>
        """)

        save = QTreeWidgetItem([f"{tr('Сохранить')} (Ctrl+S)"])
        save.setData(0, Qt.ItemDataRole.UserRole, f"""
        <h2>{tr('Сохранить')}</h2>
        <p><b>{tr('Назначение')}:</b> {tr('Сохранение текущего документа.')}</p>
        <p>{tr('Если файл сохраняется впервые, пользователю предлагается выбрать имя и расположение.')}</p>
        """)

        save_as = QTreeWidgetItem([f"{tr('Сохранить как')} (Ctrl+Shift+S)"])
        save_as.setData(0, Qt.ItemDataRole.UserRole, f"""
        <h2>{tr('Сохранить как')}</h2>
        <p>{tr('Позволяет сохранить документ под новым именем или в другой директории.')}</p>
        """)

        exit_ = QTreeWidgetItem([f"{tr('Выход')} (Alt+F4)"])
        exit_.setData(0, Qt.ItemDataRole.UserRole, f"""
        <h2>{tr('Выход')}</h2>
        <p>{tr('Завершает работу приложения.')}</p>
        <p>{tr('При наличии несохранённых изменений выводится диалог подтверждения сохранения.')}</p>
        """)

        file_menu.addChildren([create, open_, save, save_as, exit_])

        edit_menu = QTreeWidgetItem([tr("Меню Правка")])

        undo = QTreeWidgetItem([f"{tr('Отменить')} (Ctrl+Z)"])
        undo.setData(0, Qt.ItemDataRole.UserRole, f"<h2>{tr('Отменить')}</h2><p>{tr('Отмена последнего действия пользователя.')}</p>")

        redo = QTreeWidgetItem([f"{tr('Повторить')} (Ctrl+Y)"])
        redo.setData(0, Qt.ItemDataRole.UserRole, f"<h2>{tr('Повторить')}</h2><p>{tr('Повтор последнего отменённого действия.')}</p>")

        cut = QTreeWidgetItem([f"{tr('Вырезать')} (Ctrl+X)"])
        cut.setData(0, Qt.ItemDataRole.UserRole, f"<h2>{tr('Вырезать')}</h2><p>{tr('Удаляет выделенный текст и помещает его в буфер обмена.')}</p>")

        copy = QTreeWidgetItem([f"{tr('Копировать')} (Ctrl+C)"])
        copy.setData(0, Qt.ItemDataRole.UserRole, f"<h2>{tr('Копировать')}</h2><p>{tr('Копирует выделенный фрагмент в буфер обмена.')}</p>")

        paste = QTreeWidgetItem([f"{tr('Вставить')} (Ctrl+V)"])
        paste.setData(0, Qt.ItemDataRole.UserRole, f"<h2>{tr('Вставить')}</h2><p>{tr('Вставляет содержимое буфера обмена в позицию курсора.')}</p>")

        delete = QTreeWidgetItem([f"{tr('Удалить')} (Del)"])
        delete.setData(0, Qt.ItemDataRole.UserRole, f"<h2>{tr('Удалить')}</h2><p>{tr('Удаляет выделенный текст без помещения в буфер обмена.')}</p>")

        select_all = QTreeWidgetItem([f"{tr('Выделить все')} (Ctrl+A)"])
        select_all.setData(0, Qt.ItemDataRole.UserRole, f"<h2>{tr('Выделить все')}</h2><p>{tr('Выделяет весь текст в области редактирования.')}</p>")

        edit_menu.addChildren([undo, redo, cut, copy, paste, delete, select_all])

        regex_menu = QTreeWidgetItem([tr("Поиск по регулярным выражениям")])
        regex_menu.setData(0, Qt.ItemDataRole.UserRole, f"""
        <h2>{tr("Поиск по регулярным выражениям")}</h2>
        <p>{tr("help_search_intro")}</p>
        <p>{tr("help_search_panel_hint")}</p>

        <h3>{tr("Режимы поиска")}</h3>
        <ul>
            <li><b>{tr("Обычный поиск")}</b> — {tr("help_search_plain_desc")}</li>
            <li><b>{tr("Регулярные выражения")}</b> — {tr("help_search_regex_desc")}</li>
        </ul>

        <h3>{tr("Доступные типы поиска:")}</h3>
        <ul>
            <li><b>{tr("ОГРН юридического лица")}</b> - {tr("поиск 13-значных номеров, начинающихся с 1 или 5")}</li>
            <li><b>{tr("ИНН физических и юридических лиц")}</b> - {tr("help_inn_checksum")}</li>
            <li><b>{tr("Числа")}</b> - {tr("поиск целых и вещественных чисел (в т.ч. с экспоненциальной формой)")}</li>
        </ul>

        <h3>{tr("Результаты поиска")}</h3>
        <p>{tr("Результаты отображаются в таблице с колонками:")}</p>
        <ul>
            <li>{tr("Найденная подстрока")}</li>
            <li>{tr("Начальная позиция (строка, символ)")}</li>
            <li>{tr("Длина")}</li>
        </ul>
        <p>{tr("При выборе строки в таблице соответствующая подстрока подсвечивается зелёным цветом в тексте.")}</p>
        """)

        text_menu = QTreeWidgetItem([tr("Меню Текст")])

        for item_text in [tr("Постановка задачи"), tr("Грамматика"), tr("Классификация грамматики"),
                          tr("Метод анализа"), tr("Тестовый пример"), tr("Список литературы"),
                          tr("Исходный код программы")]:
            item = QTreeWidgetItem([item_text])
            item.setData(0, Qt.ItemDataRole.UserRole, f"<h2>{item_text}</h2><p>{tr('Будет реализовано в следующих работах.')}</p>")
            text_menu.addChild(item)

        run_menu = QTreeWidgetItem([tr("Меню Пуск")])
        run = QTreeWidgetItem([f"{tr('Запустить анализатор')} (F5)"])
        run.setData(0, Qt.ItemDataRole.UserRole, f"""
        <h2>{tr('Запустить анализатор')}</h2>
        <p>{tr('Предназначен для запуска лексического и синтаксического анализа текста.')}</p>
        <p>{tr('Результаты анализа выводятся в нижней области окна.')}</p>
        <p>{tr('При ошибках используется нейтрализация методом Айронса.')}</p>
        """)
        run_menu.addChild(run)

        help_menu = QTreeWidgetItem([tr("Меню Справка")])
        help_menu.setData(0, Qt.ItemDataRole.UserRole, f"""
        <h2>{tr('Меню Справка')}</h2>
        <p>{tr('Содержит руководство пользователя и информацию о программе.')}</p>
        """)

        limits = QTreeWidgetItem([tr("Ограничения")])
        limits.setData(0, Qt.ItemDataRole.UserRole, f"""
        <h2>{tr("Ограничения текущей версии")}</h2>
        <ul>
            <li>{tr("Грамматика: объявления const/var с числовым литералом.")}</li>
            <li>{tr("Подсветка синтаксиса присутствует, но базовая.")}</li>
            <li>{tr("Работа с несколькими вкладками реализована.")}</li>
            <li>{tr("Поддерживается только .txt.")}</li>
        </ul>
        """)

        self.tree.addTopLevelItems([
            general,
            file_menu,
            edit_menu,
            regex_menu,
            text_menu,
            run_menu,
            help_menu,
            limits
        ])

    def show_content(self, current, previous):
        if current:
            html = current.data(0, Qt.ItemDataRole.UserRole)
            if html:
                self.content.setHtml(html)
            else:
                self.content.clear()


class RegexSearchEngine:
    """Поиск по регулярным выражениям"""
    
    PATTERNS = {
        "ogrn": r'\b[15]\d{2}\d{2}\d{7}\d\b',
        "inn": r'\b(?:\d{10}|\d{12})\b',
        "numbers": r'(?<![\w.])[-+]?(\d+)([.,]\d+)?([eE][-+]?\d+)?(?!\w)'
    }
    
    @staticmethod
    def search_ogrn(text):
        pattern = re.compile(RegexSearchEngine.PATTERNS["ogrn"])
        return RegexSearchEngine._find_matches(text, pattern)
    
    @staticmethod
    def _inn10_checksum_ok(inn: str) -> bool:
        if len(inn) != 10 or not inn.isdigit():
            return False
        coeffs = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        s = sum(int(inn[i]) * coeffs[i] for i in range(9))
        n = s % 11
        if n == 10:
            n = 0
        return int(inn[9]) == n

    @staticmethod
    def _inn12_checksum_ok(inn: str) -> bool:
        if len(inn) != 12 or not inn.isdigit():
            return False
        c1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        s1 = sum(int(inn[i]) * c1[i] for i in range(10))
        n1 = s1 % 11
        if n1 == 10:
            n1 = 0
        if int(inn[10]) != n1:
            return False
        c2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        s2 = sum(int(inn[i]) * c2[i] for i in range(11))
        n2 = s2 % 11
        if n2 == 10:
            n2 = 0
        return int(inn[11]) == n2

    @staticmethod
    def search_inn(text):
        pattern = re.compile(RegexSearchEngine.PATTERNS["inn"])
        raw = RegexSearchEngine._find_matches(text, pattern)
        return [m for m in raw if RegexSearchEngine._inn10_checksum_ok(m["text"])
                or RegexSearchEngine._inn12_checksum_ok(m["text"])]

    @staticmethod
    def search_literal(text, needle: str):
        """Все вхождения подстроки needle (без перекрытий)."""
        if not needle:
            return []
        matches = []
        lines = text.split("\n")
        global_pos = 0
        for line_num, line in enumerate(lines, start=1):
            start = 0
            while True:
                idx = line.find(needle, start)
                if idx == -1:
                    break
                matched = line[idx : idx + len(needle)]
                matches.append(
                    {
                        "text": matched,
                        "line": line_num,
                        "char": idx + 1,
                        "length": len(matched),
                        "global_start": global_pos + idx,
                        "global_end": global_pos + idx + len(matched),
                    }
                )
                start = idx + len(needle)
            global_pos += len(line) + 1
        return matches
    
    @staticmethod
    def search_numbers(text):
        pattern = re.compile(r'(?<![\w.])[-+]?(\d+)([.,]\d+)?([eE][-+]?\d+)?(?!\w)')
        
        matches = []
        lines = text.split('\n')
        global_pos = 0
        
        for line_num, line in enumerate(lines, start=1):
            for match in pattern.finditer(line):
                num_str = match.group(0)
                is_valid = True
                
               
                if num_str.count('.') + num_str.count(',') > 1:
                    is_valid = False
                
                
                if 'e' in num_str.lower() or 'E' in num_str:
                    parts = re.split(r'[eE]', num_str, maxsplit=1)
                    if len(parts) != 2:
                        is_valid = False
                    else:
                        mantissa, exponent = parts
                        if mantissa.endswith(('.', ',')):
                            is_valid = False
                        exp_clean = exponent.lstrip('+-')
                        if not exp_clean.isdigit() or not exp_clean:
                            is_valid = False
                
            
                cleaned = num_str.lstrip('-+')
                if cleaned.startswith(('.', ',')) or cleaned.endswith(('.', ',')):
                    is_valid = False
                
                if is_valid:
                    matches.append({
                        "text": num_str,
                        "line": line_num,
                        "char": match.start() + 1,
                        "length": len(num_str),
                        "global_start": global_pos + match.start(),
                        "global_end": global_pos + match.end()
                    })
            
            global_pos += len(line) + 1
        
        return matches
            
    @staticmethod
    def _find_matches(text, pattern):
        matches = []
        
    
        lines = text.split('\n')
        
        
        global_pos = 0
        
        for line_num, line in enumerate(lines, start=1):
           
            for match in pattern.finditer(line):
                start_char = match.start() + 1  
                matched_text = match.group()
                
                matches.append({
                    "text": matched_text,
                    "line": line_num,
                    "char": start_char,
                    "length": len(matched_text),
                    "global_start": global_pos + match.start(),
                    "global_end": global_pos + match.end()
                })
            
          
            global_pos += len(line) + 1
        
        return matches
    
    @staticmethod
    def get_search_method(method_name):
        methods = {
            "ogrn": RegexSearchEngine.search_ogrn,
            "inn": RegexSearchEngine.search_inn,
            "numbers": RegexSearchEngine.search_numbers
        }
        return methods.get(method_name)


# Главное окно
class Compiler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.translator = Translator()
        self.tr = self.translator.tr

        self.setWindowTitle(self.tr("Compiler"))
        self.setMinimumSize(800, 600)
        self.resize(1100, 750)

        self.current_file = None
        self.text_modified = False
        self.current_encoding = "UTF-8"
        self.insert_mode = True 

  
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.cursor_label = QLabel(self.tr("Строка: 1 : 1"))
        self.mode_label = QLabel(self.tr("Вставка"))
        self.stats_label = QLabel(f"0 {self.tr('символов')} | 0 {self.tr('слов')}")
        self.encoding_label = QLabel(self.tr("UTF-8"))

        self.statusBar.addPermanentWidget(self.cursor_label)
        self.statusBar.addPermanentWidget(self.mode_label)
        self.statusBar.addPermanentWidget(self.stats_label)
        self.statusBar.addPermanentWidget(self.encoding_label)
        self.statusBar.showMessage(self.tr("Готово"))

        self.init_ui()
        self.create_actions()
        self.create_menus()
        self.create_toolbar()

        self.editor.textChanged.connect(self.on_text_changed)
        self.editor.cursorPositionChanged.connect(self.update_cursor_position)


        self.stats_timer = QTimer(self)
        self.stats_timer.setSingleShot(True)
        self.stats_timer.timeout.connect(self.update_text_stats)
        self.editor.textChanged.connect(lambda: self.stats_timer.start(300))

        self.update_cursor_position()
        self.update_text_stats()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(self.splitter)

        self.editor = CodeEditor()
        self.highlighter = SimpleSyntaxHighlighter(self.editor.document())
        self.splitter.addWidget(self.editor)


        self.search_panel_group = QGroupBox(self.tr("Поиск"))
        self.search_panel_group.setVisible(False)
        sp_main = QVBoxLayout(self.search_panel_group)

        row_input = QHBoxLayout()
        self.search_input_label = QLabel(self.tr("Строка для поиска:"))
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self.perform_search)
        row_input.addWidget(self.search_input_label)
        row_input.addWidget(self.search_input, 1)

        row_mode = QHBoxLayout()
        self.search_mode_label = QLabel(self.tr("Режим:"))
        self.search_mode_combo = QComboBox()
        self.search_mode_combo.addItem(self.tr("Обычный поиск"), "plain")
        self.search_mode_combo.addItem(self.tr("Регулярные выражения"), "regex")
        self.search_mode_combo.currentIndexChanged.connect(self._on_search_mode_changed)
        row_mode.addWidget(self.search_mode_label)
        row_mode.addWidget(self.search_mode_combo, 1)

        row_regex = QHBoxLayout()
        self.regex_subtype_label = QLabel(self.tr("Тип шаблона:"))
        self.regex_combo = QComboBox()
        self.regex_combo.addItem(self.tr("ОГРН юридического лица"), "ogrn")
        self.regex_combo.addItem(self.tr("ИНН (физ. и юр. лиц)"), "inn")
        self.regex_combo.addItem(self.tr("Числа (целые, вещественные, экспонента)"), "numbers")
        row_regex.addWidget(self.regex_subtype_label)
        row_regex.addWidget(self.regex_combo, 1)

        row_btns = QHBoxLayout()
        self.search_button = QPushButton(self.tr("Найти"))
        self.search_button.clicked.connect(self.perform_search)
        self.search_button.setMinimumWidth(100)
        self.clear_search_button = QPushButton(self.tr("Очистить"))
        self.clear_search_button.clicked.connect(self.clear_search_results)
        self.clear_search_button.setMinimumWidth(100)
        self.close_search_panel_button = QPushButton(self.tr("Закрыть"))
        self.close_search_panel_button.clicked.connect(self.hide_search_panel)
        self.close_search_panel_button.setMinimumWidth(100)
        self.match_count_label = QLabel("0")
        row_btns.addWidget(self.search_button)
        row_btns.addWidget(self.clear_search_button)
        row_btns.addWidget(self.close_search_panel_button)
        row_btns.addStretch()
        row_btns.addWidget(QLabel(self.tr("Найдено:")))
        row_btns.addWidget(self.match_count_label)

        sp_main.addLayout(row_input)
        sp_main.addLayout(row_mode)
        sp_main.addLayout(row_regex)
        sp_main.addLayout(row_btns)

        self._on_search_mode_changed()
        
        self.results_widget = QWidget()
        results_layout = QVBoxLayout(self.results_widget)
        self.results_tabs = QTabWidget()

        self.tokens_table = QTableWidget()
        self.tokens_table.setColumnCount(4)
        self.tokens_table.setHorizontalHeaderLabels([
            self.tr("Условный код"),
            self.tr("Тип лексемы"),
            self.tr("Лексема"),
            self.tr("Местоположение")
        ])
        self.tokens_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tokens_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_tabs.addTab(self.tokens_table, self.tr("Лексемы"))

        self.ast_output = QPlainTextEdit()
        self.ast_output.setReadOnly(True)
        self.ast_output.setFont(QFont("Courier New", 9))
        self.ast_output.setPlaceholderText(self.tr("ast_placeholder"))
        self.ast_tab = QWidget()
        ast_tab_layout = QVBoxLayout(self.ast_tab)
        ast_tab_layout.setContentsMargins(0, 0, 0, 0)
        ast_tab_layout.addWidget(self.ast_output, 1)
        self.btn_show_ast = QPushButton(self.tr("Показать AST"))
        self.btn_show_ast.clicked.connect(self.show_ast_visualization)
        ast_tab_layout.addWidget(self.btn_show_ast)
        self.results_tabs.addTab(self.ast_tab, self.tr("AST"))

        self.errors_table = QTableWidget()
        self.errors_table.setColumnCount(3)
        self.errors_table.setHorizontalHeaderLabels([
            self.tr("Неверный фрагмент"),
            self.tr("Местоположение"),
            self.tr("Описание"),
        ])
        self.errors_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.errors_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.errors_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.errors_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.errors_table.cellClicked.connect(self.go_to_error)
        self.results_tabs.addTab(self.errors_table, self.tr("Ошибки"))

        self.regex_results_table = QTableWidget()
        self.regex_results_table.setColumnCount(3)
        self.regex_results_table.setHorizontalHeaderLabels([
            self.tr("Найденная подстрока"),
            self.tr("Начальная позиция"),
            self.tr("Длина")
        ])
        self.regex_results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.regex_results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.regex_results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.regex_results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.regex_results_table.itemSelectionChanged.connect(self.on_regex_result_selected)
        self.results_tabs.addTab(self.regex_results_table, self.tr("Результаты поиска"))

        self.syntax_error_count_label = QLabel()
        self.syntax_error_count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.syntax_status_label = QLabel()
        self.syntax_status_label.setWordWrap(True)

        results_layout.addWidget(self.search_panel_group)
        results_layout.addWidget(self.syntax_status_label)
        results_layout.addWidget(self.results_tabs)
        results_layout.addWidget(self.syntax_error_count_label)
        self.splitter.addWidget(self.results_widget)
        self.splitter.setSizes([450, 250])

    def _on_search_mode_changed(self, _index=None):
        is_regex = self.search_mode_combo.currentData() == "regex"
        self.regex_subtype_label.setVisible(is_regex)
        self.regex_combo.setVisible(is_regex)
        self.search_input.setEnabled(not is_regex)
        if is_regex:
            self.search_input.setPlaceholderText(self.tr("В режиме РВ поле не используется"))
        else:
            self.search_input.setPlaceholderText(self.tr("Введите подстроку"))

    def toggle_search_panel(self):
        vis = not self.search_panel_group.isVisible()
        self.search_panel_group.setVisible(vis)
        if vis:
            self.search_input.setFocus()
        else:
            self.editor.setFocus()

    def hide_search_panel(self):
        self.search_panel_group.setVisible(False)
        self.editor.setFocus()

    def perform_search(self):
        """Обычный поиск подстроки или поиск по встроенным шаблонам РВ."""
        text = self.editor.toPlainText()

        if not text.strip():
            QMessageBox.information(self, self.tr("Поиск"), self.tr("Нет данных для поиска"))
            return

        self.clear_search_results()

        mode = self.search_mode_combo.currentData()
        matches = []

        if mode == "plain":
            needle = self.search_input.text()
            if not needle:
                QMessageBox.information(
                    self, self.tr("Поиск"), self.tr("Укажите подстроку для поиска")
                )
                return
            matches = RegexSearchEngine.search_literal(text, needle)
            search_name = self.tr("Обычный поиск")
        else:
            search_type = self.regex_combo.currentData()
            if search_type == "ogrn":
                matches = RegexSearchEngine.search_ogrn(text)
                search_name = self.tr("ОГРН")
            elif search_type == "inn":
                matches = RegexSearchEngine.search_inn(text)
                search_name = self.tr("ИНН")
            elif search_type == "numbers":
                matches = RegexSearchEngine.search_numbers(text)
                search_name = self.tr("Числа")
            else:
                return

        self.display_regex_results(matches)

        self.match_count_label.setText(str(len(matches)))

        if matches:
            self.statusBar.showMessage(
                self.tr("Найдено {0} совпадений для типа '{1}'").format(len(matches), search_name)
            )
        else:
            self.statusBar.showMessage(
                self.tr("Совпадений для типа '{0}' не найдено").format(search_name)
            )

        if matches:
            self.results_tabs.setCurrentIndex(3)  
    
    def display_regex_results(self, matches):
        """Отображает результаты поиска в таблице"""
        self.regex_results_table.setRowCount(0)
        
        for match in matches:
            row = self.regex_results_table.rowCount()
            self.regex_results_table.insertRow(row)
            
            self.regex_results_table.setItem(row, 0, QTableWidgetItem(match["text"]))
            
            position = self.tr("строка {0}, символ {1}").format(match["line"], match["char"])
            pos_item = QTableWidgetItem(position)
            pos_item.setData(Qt.ItemDataRole.UserRole, match) 
            self.regex_results_table.setItem(row, 1, pos_item)
            
            self.regex_results_table.setItem(row, 2, QTableWidgetItem(str(match["length"])))
        
        self.regex_results_table.resizeColumnsToContents()
    
    def on_regex_result_selected(self):
        selected_rows = self.regex_results_table.selectedItems()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        pos_item = self.regex_results_table.item(row, 1)
        if not pos_item:
            return
        
        match_data = pos_item.data(Qt.ItemDataRole.UserRole)
        if not match_data:
            return
        
        self.editor.highlight_substring(
            match_data["line"],
            match_data["char"],
            match_data["length"]
        )
    
    def clear_search_results(self):
        self.regex_results_table.setRowCount(0)
        self.match_count_label.setText("0")
        self.editor.clear_highlights()
        self.statusBar.showMessage(self.tr("Результаты поиска очищены"))
    
    def go_to_error(self, row, column):
        item = self.errors_table.item(row, 0)
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, (list, tuple)) and len(data) >= 3:
            line, col, frag_len = int(data[0]), int(data[1]), int(data[2])
        else:
            try:
                loc = self.errors_table.item(row, 1).text()
                line, col = self._parse_location_cell(loc)
                frag_len = 1
            except (ValueError, TypeError, AttributeError):
                return

        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(line - 1):
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.MoveAnchor,
            col - 1,
        )
        if frag_len > 0:
            cursor.movePosition(
                QTextCursor.MoveOperation.Right,
                QTextCursor.MoveMode.KeepAnchor,
                frag_len,
            )

        self.editor.setTextCursor(cursor)
        self.editor.setFocus()
        self.editor.centerCursor()

    def _parse_location_cell(self, loc: str):
        m = re.search(r"строка\s+(\d+).*?позици[яи]\s+(\d+)", loc, re.IGNORECASE)
        if m:
            return int(m.group(1)), int(m.group(2))
        m2 = re.search(r"line\s+(\d+).*?position\s+(\d+)", loc, re.IGNORECASE)
        if m2:
            return int(m2.group(1)), int(m2.group(2))
        return 1, 1

    def create_actions(self):
        self.act_new = QAction(self.tr("Создать"), self)
        self.act_new.setShortcut(QKeySequence("Ctrl+N"))
        self.act_new.triggered.connect(self.new_file)

        self.act_open = QAction(self.tr("Открыть"), self)
        self.act_open.setShortcut(QKeySequence("Ctrl+O"))
        self.act_open.triggered.connect(self.open_file)

        self.act_save = QAction(self.tr("Сохранить"), self)
        self.act_save.setShortcut(QKeySequence("Ctrl+S"))
        self.act_save.triggered.connect(self.save_file)

        self.act_save_as = QAction(self.tr("Сохранить как"), self)
        self.act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.act_save_as.triggered.connect(self.save_as_file)

        self.act_exit = QAction(self.tr("Выход"), self)
        self.act_exit.setShortcut(QKeySequence("Alt+F4"))
        self.act_exit.triggered.connect(self.close)

        self.act_undo = QAction(self.tr("Отменить"), self)
        self.act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        self.act_undo.triggered.connect(self.editor.undo)

        self.act_redo = QAction(self.tr("Повторить"), self)
        self.act_redo.setShortcut(QKeySequence("Ctrl+Y"))
        self.act_redo.triggered.connect(self.editor.redo)

        self.act_cut = QAction(self.tr("Вырезать"), self)
        self.act_cut.setShortcut(QKeySequence("Ctrl+X"))
        self.act_cut.triggered.connect(self.editor.cut)

        self.act_copy = QAction(self.tr("Копировать"), self)
        self.act_copy.setShortcut(QKeySequence("Ctrl+C"))
        self.act_copy.triggered.connect(self.editor.copy)

        self.act_paste = QAction(self.tr("Вставить"), self)
        self.act_paste.setShortcut(QKeySequence("Ctrl+V"))
        self.act_paste.triggered.connect(self.editor.paste)

        self.act_delete = QAction(self.tr("Удалить"), self)
        self.act_delete.setShortcut(QKeySequence("Del"))
        self.act_delete.triggered.connect(lambda: self.editor.textCursor().removeSelectedText())

        self.act_select_all = QAction(self.tr("Выделить все"), self)
        self.act_select_all.setShortcut(QKeySequence("Ctrl+A"))
        self.act_select_all.triggered.connect(self.editor.selectAll)

        self.act_search_panel = QAction(self.tr("Поиск"), self)
        self.act_search_panel.setShortcut(QKeySequence("Ctrl+F"))
        self.act_search_panel.triggered.connect(self.toggle_search_panel)

        self.act_run = QAction(self.tr("Пуск"), self)
        self.act_run.setShortcut(QKeySequence("F5"))
        self.act_run.triggered.connect(self.run_analyzer)

        self.act_task     = QAction(self.tr("Постановка задачи"), self)
        self.act_grammar  = QAction(self.tr("Грамматика"), self)
        self.act_classify = QAction(self.tr("Классификация грамматики"), self)
        self.act_method   = QAction(self.tr("Метод анализа"), self)
        self.act_example  = QAction(self.tr("Тестовый пример"), self)
        self.act_refs     = QAction(self.tr("Список литературы"), self)
        self.act_source   = QAction(self.tr("Исходный код программы"), self)

        for act in [self.act_task, self.act_grammar, self.act_classify,
                    self.act_method, self.act_example, self.act_refs, self.act_source]:
            act.triggered.connect(lambda _, t=act.text(): self.show_placeholder(t))

        self.act_help = QAction(self.tr("Вызов справки"), self)
        self.act_help.setShortcut(QKeySequence("F1"))
        self.act_help.triggered.connect(self.show_help)

        self.act_about = QAction(self.tr("О программе"), self)
        self.act_about.triggered.connect(self.show_about)

        self.act_lang_ru = QAction(self.tr("Русский"), self)
        self.act_lang_ru.triggered.connect(lambda: self.change_language("ru"))

        self.act_lang_en = QAction(self.tr("English"), self)
        self.act_lang_en.triggered.connect(lambda: self.change_language("en"))

    def create_menus(self):
        mb = self.menuBar()

        self.menu_file = mb.addMenu(self.tr("Файл"))
        self.menu_file.addAction(self.act_new)
        self.menu_file.addAction(self.act_open)
        self.menu_file.addAction(self.act_save)
        self.menu_file.addAction(self.act_save_as)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.act_exit)

        self.menu_edit = mb.addMenu(self.tr("Правка"))
        self.menu_edit.addAction(self.act_undo)
        self.menu_edit.addAction(self.act_redo)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.act_cut)
        self.menu_edit.addAction(self.act_copy)
        self.menu_edit.addAction(self.act_paste)
        self.menu_edit.addAction(self.act_delete)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.act_select_all)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.act_search_panel)

        self.menu_text = mb.addMenu(self.tr("Текст"))
        self.menu_text.addAction(self.act_task)
        self.menu_text.addAction(self.act_grammar)
        self.menu_text.addAction(self.act_classify)
        self.menu_text.addAction(self.act_method)
        self.menu_text.addAction(self.act_example)
        self.menu_text.addAction(self.act_refs)
        self.menu_text.addAction(self.act_source)

        self.menu_run = mb.addMenu(self.tr("Пуск"))
        self.menu_run.addAction(self.act_run)

        self.menu_lang = mb.addMenu(self.tr("Язык"))
        self.menu_lang.addAction(self.act_lang_ru)
        self.menu_lang.addAction(self.act_lang_en)

        self.menu_help = mb.addMenu(self.tr("Справка"))
        self.menu_help.addAction(self.act_help)
        self.menu_help.addAction(self.act_about)

    def create_toolbar(self):
        tb = QToolBar(self.tr("Панель инструментов"))
        self.addToolBar(tb)
        self.main_toolbar = tb
        tb.setIconSize(QSize(28, 28))

        style = self.style()
        pix = QStyle.StandardPixmap

        items = [
            (pix.SP_FileDialogContentsView, "Поиск", self.toggle_search_panel),
            (pix.SP_MediaPlay,          "Пуск анализатора",      self.run_analyzer),
            (pix.SP_FileIcon,           "Создать",               self.new_file),
            (pix.SP_DirOpenIcon,        "Открыть",               self.open_file),
            (pix.SP_DialogSaveButton,   "Сохранить",             self.save_file),
            (pix.SP_ArrowBack,          "Отменить",              self.editor.undo),
            (pix.SP_ArrowForward,       "Повторить",             self.editor.redo),
            (pix.SP_DialogCancelButton, "Вырезать",              self.editor.cut),
            (pix.SP_DriveFDIcon,        "Копировать",            self.editor.copy),
            (pix.SP_DialogOkButton,     "Вставить",              self.editor.paste),
            (pix.SP_MessageBoxQuestion, "Справка",               self.show_help),
            (pix.SP_MessageBoxInformation, "О программе",     self.show_about),
        ]

        self.toolbar_actions = []
        for icon_enum, tip_key, func in items:
            icon = style.standardIcon(icon_enum)
            act = QAction(icon, self.tr(tip_key), self)
            act.triggered.connect(func)
            tb.addAction(act)
            self.toolbar_actions.append((act, tip_key))

    def change_language(self, lang):
        self.translator.set_language(lang)
        self.retranslate_ui()

        self.setWindowTitle("")
        QApplication.processEvents()
        self.update_window_title()
        self.menuBar().repaint()
        self.statusBar.repaint()

    def retranslate_ui(self):
        self.setWindowTitle(self.tr("Compiler"))

        self.menu_file.setTitle(self.tr("Файл"))
        self.menu_edit.setTitle(self.tr("Правка"))
        self.menu_text.setTitle(self.tr("Текст"))
        self.menu_run.setTitle(self.tr("Пуск"))
        self.menu_lang.setTitle(self.tr("Язык"))
        self.menu_help.setTitle(self.tr("Справка"))

        self.act_new.setText(self.tr("Создать"))
        self.act_open.setText(self.tr("Открыть"))
        self.act_save.setText(self.tr("Сохранить"))
        self.act_save_as.setText(self.tr("Сохранить как"))
        self.act_exit.setText(self.tr("Выход"))
        self.act_undo.setText(self.tr("Отменить"))
        self.act_redo.setText(self.tr("Повторить"))
        self.act_cut.setText(self.tr("Вырезать"))
        self.act_copy.setText(self.tr("Копировать"))
        self.act_paste.setText(self.tr("Вставить"))
        self.act_delete.setText(self.tr("Удалить"))
        self.act_select_all.setText(self.tr("Выделить все"))
        self.act_search_panel.setText(self.tr("Поиск"))
        self.act_run.setText(self.tr("Пуск"))
        self.act_task.setText(self.tr("Постановка задачи"))
        self.act_grammar.setText(self.tr("Грамматика"))
        self.act_classify.setText(self.tr("Классификация грамматики"))
        self.act_method.setText(self.tr("Метод анализа"))
        self.act_example.setText(self.tr("Тестовый пример"))
        self.act_refs.setText(self.tr("Список литературы"))
        self.act_source.setText(self.tr("Исходный код программы"))
        self.act_help.setText(self.tr("Вызов справки"))
        self.act_about.setText(self.tr("О программе"))
        self.act_lang_ru.setText(self.tr("Русский"))
        self.act_lang_en.setText(self.tr("English"))
        if getattr(self, "btn_show_ast", None):
            self.btn_show_ast.setText(self.tr("Показать AST"))

        if getattr(self, "main_toolbar", None):
            self.main_toolbar.setWindowTitle(self.tr("Панель инструментов"))
        for act, tip_key in getattr(self, "toolbar_actions", []):
            act.setToolTip(self.tr(tip_key))

        self.results_tabs.setTabText(0, self.tr("Лексемы"))
        self.results_tabs.setTabText(1, self.tr("AST"))
        self.results_tabs.setTabText(2, self.tr("Ошибки"))
        self.results_tabs.setTabText(3, self.tr("Результаты поиска"))

        self.tokens_table.setHorizontalHeaderLabels([
            self.tr("Условный код"),
            self.tr("Тип лексемы"),
            self.tr("Лексема"),
            self.tr("Местоположение"),
        ])
        self.errors_table.setHorizontalHeaderLabels([
            self.tr("Неверный фрагмент"),
            self.tr("Местоположение"),
            self.tr("Описание"),
        ])
        self.regex_results_table.setHorizontalHeaderLabels([
            self.tr("Найденная подстрока"),
            self.tr("Начальная позиция"),
            self.tr("Длина")
        ])

        self.search_panel_group.setTitle(self.tr("Поиск"))
        self.search_input_label.setText(self.tr("Строка для поиска:"))
        self.search_mode_label.setText(self.tr("Режим:"))
        self.search_mode_combo.setItemText(0, self.tr("Обычный поиск"))
        self.search_mode_combo.setItemText(1, self.tr("Регулярные выражения"))
        self.regex_subtype_label.setText(self.tr("Тип шаблона:"))
        self.regex_combo.setItemText(0, self.tr("ОГРН юридического лица"))
        self.regex_combo.setItemText(1, self.tr("ИНН (физ. и юр. лиц)"))
        self.regex_combo.setItemText(2, self.tr("Числа (целые, вещественные, экспонента)"))
        self.search_button.setText(self.tr("Найти"))
        self.clear_search_button.setText(self.tr("Очистить"))
        self.close_search_panel_button.setText(self.tr("Закрыть"))
        self._on_search_mode_changed()

        self.statusBar.showMessage(self.tr("Готово") if not self.text_modified else self.tr("Изменено"))

        self.update_cursor_position()
        self.update_text_stats()

    def on_text_changed(self):
        if not self.text_modified and self.editor.toPlainText().strip():
            self.text_modified = True
            self.update_window_title()
            self.statusBar.showMessage(self.tr("Изменено"))
        self.clear_search_results()

    def update_window_title(self):
        title = self.tr("Compiler")
        if self.current_file:
            title += f" — {os.path.basename(self.current_file)}"
        if self.text_modified:
            title += " *"
        self.setWindowTitle(title)

    def update_cursor_position(self):
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.cursor_label.setText(f"{self.tr('Строка:')} {line} : {col}")

        mode = self.tr("Вставка") if not self.editor.overwrite_mode else self.tr("Замена")
        self.mode_label.setText(mode)

    def update_text_stats(self):
        text = self.editor.toPlainText()
        chars = len(text)
        words = len(text.split()) if text.strip() else 0
        self.stats_label.setText(f"{chars} {self.tr('символов')} | {words} {self.tr('слов')}")

    def maybe_save(self) -> bool:
        if not self.text_modified:
            return True

        reply = QMessageBox.question(
            self,
            self.tr("Сохранить изменения?"),
            self.tr("Есть несохранённые изменения.\nСохранить?"),
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No |
            QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Yes:
            return self.save_file()
        return reply != QMessageBox.StandardButton.Cancel

    def new_file(self):
        if self.maybe_save():
            self.editor.clear()
            self.current_file = None
            self.text_modified = False
            self.update_window_title()
            self.statusBar.showMessage(self.tr("Новый документ"))

    def open_file(self):
        if not self.maybe_save():
            return
        fname, _ = QFileDialog.getOpenFileName(
            self, self.tr("Открыть"), "", self.tr("file_filter_txt")
        )
        if fname:
            try:
                with open(fname, encoding='utf-8') as f:
                    self.editor.setPlainText(f.read())
                self.current_file = fname
                self.text_modified = False
                self.update_window_title()
                self.statusBar.showMessage(f"{self.tr('Открыт:')} {os.path.basename(fname)}")
            except Exception as e:
                QMessageBox.warning(self, self.tr("Ошибка"), f"{self.tr('Не удалось открыть')}:\n{e}")

    def save_file(self) -> bool:
        if not self.current_file:
            return self.save_as_file()
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.text_modified = False
            self.update_window_title()
            self.statusBar.showMessage(self.tr("Сохранено"))
            return True
        except Exception as e:
            QMessageBox.warning(self, self.tr("Ошибка"), f"{self.tr('Не удалось сохранить')}:\n{e}")
            return False

    def save_as_file(self) -> bool:
        fname, _ = QFileDialog.getSaveFileName(
            self, self.tr("Сохранить как"), "", self.tr("file_filter_txt")
        )
        if fname:
            self.current_file = fname
            return self.save_file()
        return False

    def closeEvent(self, event):
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()

    def show_ast_visualization(self):
        text = self.editor.toPlainText()
        if not text.strip():
            QMessageBox.information(self, self.tr("Показать AST"), self.tr("Текст пустой"))
            return
        scanner = LexicalAnalyzer()
        tokens, lex_errors = scanner.analyze(text)
        parser = SyntaxParser(tokens)
        syn_errors, program = parser.parse()
        all_errors = list(lex_errors) + list(syn_errors)
        if all_errors:
            QMessageBox.warning(
                self,
                self.tr("ast_vis_window_title"),
                self.tr("ast_vis_parse_errors"),
            )
            return
        dlg = AstGraphDialog(program, self.tr, parent=self)
        dlg.exec()

    def run_analyzer(self):
        self.tokens_table.setRowCount(0)
        self.errors_table.setRowCount(0)
        self.ast_output.clear()
        self.syntax_status_label.clear()
        self.syntax_error_count_label.clear()

        text = self.editor.toPlainText()
        if not text.strip():
            self.statusBar.showMessage(self.tr("Текст пустой"))
            return

        scanner = LexicalAnalyzer()
        tokens, lex_errors = scanner.analyze(text)

        for t in tokens:
            row = self.tokens_table.rowCount()
            self.tokens_table.insertRow(row)
            self.tokens_table.setItem(row, 0, QTableWidgetItem(str(t["code"])))
            self.tokens_table.setItem(row, 1, QTableWidgetItem(self.tr(t["type"])))
            self.tokens_table.setItem(row, 2, QTableWidgetItem(self._tr_lexeme(t["lexeme"])))
            loc = self.tr("token_loc_fmt").format(t["line"], t["col"], t["end_col"])
            self.tokens_table.setItem(row, 3, QTableWidgetItem(loc))

        parser = SyntaxParser(tokens)
        syn_errors, program = parser.parse()

        tree_txt = format_ast_tree(program)
        json_txt = ast_to_json(program)
        self.ast_output.setPlainText(
            self.tr("ast_tree_header") + "\n\n" + (tree_txt or self.tr("ast_empty")) + "\n\n" + self.tr("ast_json_header") + "\n\n" + json_txt
        )

        all_errors = list(lex_errors) + list(syn_errors)
        for err in all_errors:
            self._append_syntax_error_row(err)

        n_err = len(all_errors)
        self.syntax_error_count_label.setText(
            self.tr("Общее количество ошибок:") + f" {n_err}"
        )

        if n_err == 0:
            self.syntax_status_label.setText(self.tr("Синтаксических ошибок не обнаружено."))
            self.statusBar.showMessage(self.tr("Анализ завершён: ошибок нет"))
            self.results_tabs.setCurrentIndex(1)
        else:
            self.syntax_status_label.setText(self.tr("Обнаружены ошибки. Отображены в таблице."))
            self.statusBar.showMessage(self.tr("Анализ завершён"))
            self.results_tabs.setCurrentIndex(2)

    def _analysis_exp(self, exp: str) -> str:
        if len(exp) == 1 and exp in "(){};:=:":
            return exp
        if exp in ("const", "var", "for", "print", "in", "int", "float"):
            return exp
        return self.tr(exp)

    def _format_analysis_msg(self, key: str, args: tuple) -> str:
        if key == "syn_expect_failed":
            exp, ctx_key, got_key = args
            exp_show = self._analysis_exp(exp)
            ctx_part = (" " + self.tr(ctx_key)) if ctx_key else ""
            got_show = self.tr(got_key) if got_key == "sym_eof" else got_key
            return self.tr("syn_expect_failed").format(exp_show, ctx_part, got_show)
        if key == "syn_err_stmt_got":
            return self.tr("syn_err_stmt_got").format(args[0])
        if key == "syn_err_block_for_print":
            return self.tr("syn_err_block_for_print").format(args[0])
        if key == "syn_err_numeric_literal":
            return self.tr("syn_err_numeric_literal")
        if key == "syn_err_expected_int_float":
            return self.tr("syn_err_expected_int_float")
        if key == "sem_dup_ident":
            return self.tr("sem_dup_ident").format(args[0], args[1])
        if key == "sem_type_mismatch":
            return self.tr("sem_type_mismatch").format(args[0], args[1])
        if key == "sem_int_out_of_range":
            return self.tr("sem_int_out_of_range").format(args[0], args[1])
        if key == "sem_range_order":
            return self.tr("sem_range_order").format(args[0], args[1])
        if key == "sem_undeclared":
            return self.tr("sem_undeclared").format(args[0])
        if key == "sem_float_invalid":
            return self.tr("sem_float_invalid")
        if key == "lex_err_bad_char":
            return self.tr("lex_err_bad_char").format(args[0])
        if args:
            return self.tr(key).format(*args)
        return self.tr(key)

    def _tr_lexeme(self, lexeme: str) -> str:
        if lexeme in ("(пробел)", "(перевод строки)", "(табуляция)"):
            return self.tr(lexeme)
        return lexeme

    def _append_syntax_error_row(self, err):
        if len(err) == 6:
            line, col, key, args, fragment, frag_len = err
            msg = self._format_analysis_msg(key, args)
        elif len(err) >= 5:
            line, col, msg, fragment, frag_len = err[:5]
            msg = self.tr(msg) if isinstance(msg, str) else str(msg)
        else:
            line, col, msg = err[:3]
            fragment = "?"
            frag_len = 1
            msg = self.tr(msg) if isinstance(msg, str) else str(msg)
        loc = self.tr("loc_fmt").format(line, col)
        row = self.errors_table.rowCount()
        self.errors_table.insertRow(row)
        frag_item = QTableWidgetItem(str(fragment))
        frag_item.setData(Qt.ItemDataRole.UserRole, (line, col, max(frag_len, 1)))
        self.errors_table.setItem(row, 0, frag_item)
        self.errors_table.setItem(row, 1, QTableWidgetItem(loc))
        self.errors_table.setItem(row, 2, QTableWidgetItem(msg))

    def add_error(self, line: int, col: int, message: str):
        self._append_syntax_error_row((line, col, message, "?", 1))

    def show_placeholder(self, title: str):
        QMessageBox.information(self, title, f"{self.tr('Раздел')} «{title}»\n\n{self.tr('будет реализован позже')}.")

    def show_help(self):
        self.help_window = HelpWindow(self)
        self.help_window.exec()

    def show_about(self):
        QMessageBox.about(
            self,
            self.tr("О программе"),
            f"""
            <h2 align="center">{self.tr("Compiler")}</h2>
            <p align="center"><b>{self.tr("Версия 1.0")}</b></p>

            <hr>

            <h3>{self.tr("Автор")}</h3>
            <p>Княгинина Э.А.</p>

            <h3>{self.tr("Описание проекта")}</h3>
            <p>
            {self.tr("Приложение представляет собой текстовый редактор с графическим интерфейсом пользователя.")}<br>
            </p>
            
            <h3>{self.tr("Доступные типы поиска")}</h3>
            <ul>
                <li><b>{self.tr("ОГРН")}</b> - {self.tr("13 цифр, начинается с 1 или 5")}</li>
                <li><b>{self.tr("ИНН")}</b> - {self.tr("10 цифр (юр. лицо) или 12 цифр (физ. лицо)")}</li>
                <li><b>{self.tr("Числа")}</b> - {self.tr("целые, вещественные (.,), экспоненциальная форма")}</li>
            </ul>

            <h3>{self.tr("Используемые технологии")}</h3>
            <ul>
                <li><b>{self.tr("Язык программирования")}:</b> Python 3</li>
                <li><b>{self.tr("GUI-фреймворк")}:</b> PyQt6</li>
                <li><b>{self.tr("Регулярные выражения")}:</b> re</li>
            </ul>

            <h3>{self.tr("Год выполнения")}</h3>
            <p>2026</p>
            """
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Compiler()
    window.show()
    sys.exit(app.exec())