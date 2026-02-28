import sys
import os

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
    QLabel
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
    QSyntaxHighlighter  
)

from PyQt6.QtCore import Qt, QSize, QRect, QRegularExpression, QTimer
from translations import Translator


# Нумерация строк
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

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width()
        self.highlight_current_line()

        # Режим вставки/замены
        self.overwrite_mode = False

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
        extra = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(230, 230, 255))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra.append(selection)
        self.setExtraSelections(extra)

    def keyPressEvent(self, event):
        if self.overwrite_mode and not event.modifiers() and len(event.text()) > 0:
            cursor = self.textCursor()
            if not cursor.hasSelection() and not cursor.atBlockEnd():
                cursor.deleteChar()
        super().keyPressEvent(event)


# Подсветка синтаксиса 
from PyQt6.QtGui import QSyntaxHighlighter


class SimpleSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        keywords = ['var', 'const', 'if', 'else', 'while', 'for', 'return', 'true', 'false']
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        self.highlighting_rules.append((QRegularExpression(r"//.*"), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


# Окно справки 
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
        <p>{tr('Предназначен для запуска синтаксического анализа текста.')}</p>
        <p>{tr('Результаты анализа выводятся в нижней области окна.')}</p>
        <p>{tr('В текущей лабораторной работе анализатор реализован как заглушка.')}</p>
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
            <li>{tr("Синтаксический анализатор не реализован.")}</li>
            <li>{tr("Подсветка синтаксиса присутствует, но базовая.")}</li>
            <li>{tr("Работа с несколькими вкладками реализована.")}</li>
            <li>{tr("Поддерживается только .txt.")}</li>
        </ul>
        """)

        self.tree.addTopLevelItems([
            general,
            file_menu,
            edit_menu,
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
        self.insert_mode = True  # True = Вставка, False = Замена

        # Статусная строка
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

        # Таймер для статистики
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
        highlighter = SimpleSyntaxHighlighter(self.editor.document())  # ← подсветка подключается здесь
        self.splitter.addWidget(self.editor)

        # Область результатов
        self.results_widget = QWidget()
        results_layout = QVBoxLayout(self.results_widget)
        self.results_tabs = QTabWidget()

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 11))
        self.results_tabs.addTab(self.output, self.tr("Результаты"))

        self.errors_table = QTableWidget()
        self.errors_table.setColumnCount(3)
        self.errors_table.setHorizontalHeaderLabels([self.tr("Строка"), self.tr("Позиция"), self.tr("Сообщение")])
        self.errors_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.errors_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_tabs.addTab(self.errors_table, self.tr("Ошибки"))

        results_layout.addWidget(self.results_tabs)
        self.splitter.addWidget(self.results_widget)

        self.splitter.setSizes([550, 200])

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
        tb = QToolBar("Панель инструментов")
        self.addToolBar(tb)
        tb.setIconSize(QSize(28, 28))

        style = self.style()
        pix = QStyle.StandardPixmap

        items = [
            (pix.SP_MediaPlay,          self.tr("Пуск анализатора"),      self.run_analyzer),
            (pix.SP_FileIcon,           self.tr("Создать"),               self.new_file),
            (pix.SP_DirOpenIcon,        self.tr("Открыть"),               self.open_file),
            (pix.SP_DialogSaveButton,   self.tr("Сохранить"),             self.save_file),
            (pix.SP_ArrowBack,          self.tr("Отменить"),              self.editor.undo),
            (pix.SP_ArrowForward,       self.tr("Повторить"),             self.editor.redo),
            (pix.SP_DialogCancelButton, self.tr("Вырезать"),              self.editor.cut),
            (pix.SP_DriveFDIcon,        self.tr("Копировать"),            self.editor.copy),
            (pix.SP_DialogOkButton,     self.tr("Вставить"),              self.editor.paste),
            (pix.SP_MessageBoxQuestion, self.tr("Справка"),               self.show_help),
            (pix.SP_MessageBoxInformation, self.tr("О программе"),     self.show_about),
        ]

        for icon_enum, tooltip, func in items:
            icon = style.standardIcon(icon_enum)
            act = QAction(icon, tooltip, self)
            act.triggered.connect(func)
            tb.addAction(act)

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
        self.act_run.setText(self.tr("Пуск"))
        self.act_help.setText(self.tr("Вызов справки"))
        self.act_about.setText(self.tr("О программе"))
        self.act_lang_ru.setText(self.tr("Русский"))
        self.act_lang_en.setText(self.tr("English"))

        self.results_tabs.setTabText(0, self.tr("Результаты"))
        self.results_tabs.setTabText(1, self.tr("Ошибки"))
        self.errors_table.setHorizontalHeaderLabels([
            self.tr("Строка"),
            self.tr("Позиция"),
            self.tr("Сообщение")
        ])

        self.statusBar.showMessage(self.tr("Готово") if not self.text_modified else self.tr("Изменено"))

        self.update_cursor_position()
        self.update_text_stats()

    def on_text_changed(self):
        if not self.text_modified and self.editor.toPlainText().strip():
            self.text_modified = True
            self.update_window_title()
            self.statusBar.showMessage(self.tr("Изменено"))

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
        fname, _ = QFileDialog.getOpenFileName(self, self.tr("Открыть"), "", "Text files (*.txt);;All files (*.*)")
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
        fname, _ = QFileDialog.getSaveFileName(self, self.tr("Сохранить как"), "", "Text files (*.txt);;All files (*.*)")
        if fname:
            self.current_file = fname
            return self.save_file()
        return False

    def closeEvent(self, event):
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()

    def run_analyzer(self):
        self.output.clear()
        self.errors_table.setRowCount(0)

        text = self.editor.toPlainText().strip()
        if not text:
            self.output.append(self.tr("Текст пустой"))
            self.statusBar.showMessage(self.tr("Анализ не выполнен"))
            return

        self.output.append("Запуск анализатора...")
        self.output.append(f"{self.tr('Длина текста')}: {len(text)} {self.tr('символов')}")
        self.output.append("\n" + self.tr("Анализ завершён"))

        # Демо-ошибки
        self.add_error(5, 3, self.tr("Ожидался символ ';' после выражения"))
        self.add_error(8, 1, self.tr("Неизвестный идентификатор 'addd'"))
        self.add_error(12, 10, self.tr("Несоответствие типов"))

        self.statusBar.showMessage(self.tr("Анализ завершён"))

    def add_error(self, line: int, col: int, message: str):
        row = self.errors_table.rowCount()
        self.errors_table.insertRow(row)
        self.errors_table.setItem(row, 0, QTableWidgetItem(str(line)))
        self.errors_table.setItem(row, 1, QTableWidgetItem(str(col)))
        self.errors_table.setItem(row, 2, QTableWidgetItem(message))

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
            <p align="center"><b>Версия 1.0</b></p>

            <hr>

            <h3>{self.tr("Автор")}</h3>
            <p>Княгинина Э.А.</p>

            <h3>{self.tr("Описание проекта")}</h3>
            <p>
            {self.tr("Приложение представляет собой текстовый редактор с графическим интерфейсом пользователя.")}<br>
            {self.tr("В дальнейшем программа будет дополнена функциями языкового процессора.")}
            </p>

            <h3>{self.tr("Используемые технологии")}</h3>
            <ul>
                <li><b>{self.tr("Язык программирования")}:</b> Python 3</li>
                <li><b>{self.tr("GUI-фреймворк")}:</b> PyQt6</li>
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