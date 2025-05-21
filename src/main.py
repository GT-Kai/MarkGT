import sys
import os
import traceback
import datetime
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QMenuBar, QMenu, QFileDialog, QMessageBox, QToolBar, QStatusBar, QTextBrowser)
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtGui import QIcon, QAction
from editor import Editor
import mistune

SINGLE_INSTANCE_KEY = "MarkGT_SingleInstance"

def is_another_instance_running():
    socket = QLocalSocket()
    socket.connectToServer(SINGLE_INSTANCE_KEY)
    if socket.waitForConnected(100):
        if len(sys.argv) > 1:
            msg = sys.argv[1]
            socket.write(msg.encode("utf-8"))
            socket.flush()
            socket.waitForBytesWritten(100)
        socket.disconnectFromServer()
        return True
    return False

def create_single_instance_server(window):
    QLocalServer.removeServer(SINGLE_INSTANCE_KEY)
    server = QLocalServer()
    server.listen(SINGLE_INSTANCE_KEY)
    def on_new_connection():
        client = server.nextPendingConnection()
        if client and client.waitForReadyRead(100):
            msg = client.readAll().data().decode("utf-8").strip()
            if msg and os.path.exists(msg):
                window.editor.open_file(msg)
                window.current_file_path = msg
                window.is_dirty = False
                window.update_window_title()
                window.status_bar.showMessage(f'已打开文件: {msg}')
                window.showNormal()
                window.activateWindow()
                window.raise_()
        client.disconnectFromServer()
    server.newConnection.connect(on_new_connection)
    return server

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file_path = None  # 添加一个变量来存储当前文件路径
        self.is_dirty = False  # 添加一个标志来跟踪文件是否被修改
        self.init_ui()
        self.setup_menu()
        self.setup_toolbar()  # 添加工具栏设置
        self.setup_menubar()
        self.setup_connections()
        # self.setup_local_server()

    def init_ui(self):
        # 设置窗口标题
        self.setWindowTitle('MarkGT')
        
        # 设置窗口图标
        if getattr(sys, 'frozen', False):
            # 打包后的路径
            icon_path = os.path.join(sys._MEIPASS, 'resources', 'icon.ico')
        else:
            # 开发环境的路径
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'icon.ico')
            
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 添加编辑器
        self.editor = Editor()
        layout.addWidget(self.editor)

        # 设置窗口大小
        self.resize(1200, 800)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪')
        
        # 显示窗口
        self.show()

    def setup_menu(self):
        # 创建菜单栏
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 新建文件
        new_action = file_menu.addAction('新建')
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        
        # 打开文件
        open_action = file_menu.addAction('打开')
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        
        # 保存文件
        save_action = file_menu.addAction('保存')
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        
        # 另存为文件
        save_as_action = file_menu.addAction('另存为')
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_file_as)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = file_menu.addAction('退出')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)

    def setup_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 添加标题按钮
        h1_action = QAction("H1", self)
        h1_action.triggered.connect(lambda: self.insert_markdown("# "))
        toolbar.addAction(h1_action)

        h2_action = QAction("H2", self)
        h2_action.triggered.connect(lambda: self.insert_markdown("## "))
        toolbar.addAction(h2_action)

        h3_action = QAction("H3", self)
        h3_action.triggered.connect(lambda: self.insert_markdown("### "))
        toolbar.addAction(h3_action)

        toolbar.addSeparator()

        # 添加列表按钮
        bullet_list_action = QAction("• 列表", self)
        bullet_list_action.triggered.connect(lambda: self.insert_markdown("- "))
        toolbar.addAction(bullet_list_action)

        number_list_action = QAction("1. 列表", self)
        number_list_action.triggered.connect(lambda: self.insert_markdown("1. "))
        toolbar.addAction(number_list_action)

        toolbar.addSeparator()

        # 添加代码按钮
        code_action = QAction("代码", self)
        code_action.triggered.connect(lambda: self.insert_markdown("```\n\n```"))
        toolbar.addAction(code_action)

        inline_code_action = QAction("行内代码", self)
        inline_code_action.triggered.connect(lambda: self.insert_markdown("`", "`"))
        toolbar.addAction(inline_code_action)

        toolbar.addSeparator()

        # 添加表格按钮
        table_action = QAction("表格", self)
        table_action.triggered.connect(self.insert_table)
        toolbar.addAction(table_action)

        toolbar.addSeparator()

        # 添加链接和图片按钮
        link_action = QAction("链接", self)
        link_action.triggered.connect(lambda: self.insert_markdown("[链接文本](" + "链接地址" + " " + "\"可选的链接标题\")"))
        toolbar.addAction(link_action)

        image_action = QAction("图片", self)
        image_action.triggered.connect(lambda: self.insert_markdown("![", "](image_url)"))
        toolbar.addAction(image_action)

    def insert_markdown(self, prefix="", suffix=""):
        """在当前光标位置插入 Markdown 语法"""
        current_tab = self.editor.get_current_tab()
        if current_tab:
            # 获取当前编辑器（可能是编辑器或预览区域）
            current_editor = self.editor.get_current_editor()
            
            if isinstance(current_editor, QTextBrowser):
                # 预览编辑模式下插入
                text_cursor = current_editor.textCursor()
                selected_text = text_cursor.selectedText()
                
                if selected_text:
                    # 如果有选中文本，替换选中文本
                    new_text = f"{prefix}{selected_text}{suffix}"
                    text_cursor.insertText(new_text)
                else:
                    # 在光标位置插入文本
                    text_cursor.insertText(prefix + suffix)
                    # 将光标移回前缀后，后缀前
                    if suffix:
                        position = text_cursor.position()
                        text_cursor.setPosition(position - len(suffix))
                        current_editor.setTextCursor(text_cursor)
                
                # 确保编辑器获得焦点
                current_editor.setFocus()
            else:
                # 原始编辑器模式
                editor = current_tab['editor']
                
                # 获取当前光标位置
                line, index = editor.getCursorPosition()
                
                # 获取选中的文本
                if editor.hasSelectedText():
                    # 获取选中文本的起始和结束位置
                    start_line, start_index = editor.getSelectionStart()
                    end_line, end_index = editor.getSelectionEnd()
                    # 获取选中的文本
                    selected_text = editor.selectedText()
                    # 删除选中的文本
                    editor.setSelection(start_line, start_index, end_line, end_index)
                    editor.replaceSelectedText(f"{prefix}{selected_text}{suffix}")
                else:
                    # 在光标位置插入文本
                    editor.insert(f"{prefix}{suffix}")
                    # 将光标移动到插入的前缀之后，后缀之前
                    if suffix:
                        editor.setCursorPosition(line, index + len(prefix))
                    else:
                        # 将光标移动到插入的文本之后
                        editor.setCursorPosition(line, index + len(prefix))

    def insert_table(self):
        """插入一个基本的 Markdown 表格"""
        table_template = """| 标题1 | 标题2 | 标题3 |
|-------|-------|-------|
| 内容1 | 内容2 | 内容3 |
| 内容4 | 内容5 | 内容6 |
"""
        current_tab = self.editor.get_current_tab()
        if current_tab:
            # 获取当前编辑器（可能是编辑器或预览区域）
            current_editor = self.editor.get_current_editor()
            
            if isinstance(current_editor, QTextBrowser):
                # 预览编辑模式下插入
                text_cursor = current_editor.textCursor()
                text_cursor.insertText(table_template)
                
                # 确保编辑器获得焦点
                current_editor.setFocus()
            else:
                # 原始编辑器模式
                editor = current_tab['editor']
                
                # 获取当前光标位置
                line, index = editor.getCursorPosition()
                
                # 在光标位置插入表格模板
                editor.insert(table_template)
                
                # 将光标移动到插入的表格之后
                editor.setCursorPosition(line + 4, 0)  # 移动到表格后的新行

    def setup_connections(self):
        # 连接标签页切换信号
        self.editor.tab_widget.currentChanged.connect(self.tab_changed)

    def tab_changed(self, index):
        if index >= 0 and index in self.editor.tabs:
            # 更新当前文件路径
            self.current_file_path = self.editor.tabs[index]['file_path']
            # 更新窗口标题
            self.update_window_title()
        else:
            # 如果没有标签页，重置状态
            self.current_file_path = None
            self.is_dirty = False
            self.update_window_title()

    def document_modified(self):
        if not self.is_dirty:
            self.is_dirty = True
            self.update_window_title()

    def update_window_title(self):
        base_title = 'MarkGT'
        if self.current_file_path:
            file_name = os.path.basename(self.current_file_path)
            title = f'{base_title} - {file_name}'
        else:
            title = base_title

        if self.is_dirty:
            self.setWindowTitle(f'{title}*')
        else:
            self.setWindowTitle(title)

    def new_file(self):
        if self.is_dirty:
            reply = QMessageBox.question(self, '新建文件',
                                       '是否保存当前文件？',
                                       QMessageBox.StandardButton.Yes |
                                       QMessageBox.StandardButton.No |
                                       QMessageBox.StandardButton.Cancel)
            
            if reply == QMessageBox.StandardButton.Yes:
                if not self.save_file(): # 如果保存失败，则取消新建
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return
                
        # 创建新标签页
        self.editor.create_new_tab()
        self.current_file_path = None
        self.is_dirty = False
        self.update_window_title()

    def open_file(self):
        if self.is_dirty:
            reply = QMessageBox.question(self, '打开文件',
                                       '是否保存当前文件？',
                                       QMessageBox.StandardButton.Yes |
                                       QMessageBox.StandardButton.No |
                                       QMessageBox.StandardButton.Cancel)
            
            if reply == QMessageBox.StandardButton.Yes:
                if not self.save_file(): # 如果保存失败，则取消打开
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        file_name, _ = QFileDialog.getOpenFileName(self, '打开文件',
                                                 '', 'Markdown Files (*.md);;All Files (*.*)')
        if file_name:
            if self.editor.open_file(file_name):
                self.current_file_path = file_name
                self.is_dirty = False
                self.update_window_title()
                # 检查文件是否已经打开
                for tab_index, tab_info in self.editor.tabs.items():
                    if tab_info['file_path'] == file_name and tab_index != self.editor.tab_widget.currentIndex():
                        self.status_bar.showMessage(f'文件已打开，已切换到对应标签页')
                    else:
                        self.status_bar.showMessage(f'已打开文件: {file_name}')
            else:
                QMessageBox.warning(self, '错误', '无法打开文件')

    def save_file(self):
        current_index = self.editor.tab_widget.currentIndex()
        if current_index >= 0:
            if self.editor.save_file(current_index):
                self.is_dirty = False
                self.update_window_title()
                self.status_bar.showMessage('文件已保存')
                return True
            else:
                QMessageBox.warning(self, '错误', '无法保存文件')
                return False
        return False

    def save_file_as(self):
        current_index = self.editor.tab_widget.currentIndex()
        if current_index >= 0:
            if self.editor.save_file_as(current_index):
                self.is_dirty = False
                self.update_window_title()
                self.status_bar.showMessage('文件已保存')
                return True
            else:
                QMessageBox.warning(self, '错误', '无法保存文件')
                return False
        return False

    def closeEvent(self, event):
        if self.is_dirty:
            reply = QMessageBox.question(self, '退出',
                                       '文件未保存，是否退出？',
                                       QMessageBox.StandardButton.Yes |
                                       QMessageBox.StandardButton.No |
                                       QMessageBox.StandardButton.Cancel)
            
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def setup_menubar(self):
        # 创建菜单栏
        menubar = self.menuBar()
        
        # 创建视图菜单
        view_menu = menubar.addMenu("视图")
        
        # 添加预览编辑模式切换
        preview_edit_action = QAction("预览编辑", self)
        preview_edit_action.setCheckable(True)
        preview_edit_action.setShortcut("Ctrl+E")
        preview_edit_action.triggered.connect(self.toggle_preview_edit_mode)
        view_menu.addAction(preview_edit_action)
        
        # 添加目录栏显示切换
        toc_action = QAction("显示目录栏", self)
        toc_action.setCheckable(True)
        toc_action.setChecked(True)
        toc_action.triggered.connect(self.toggle_toc_visible)
        view_menu.addAction(toc_action)
        self.toc_action = toc_action  # 保存引用，便于后续操作
        
        # 添加自动换行动作
        wrap_action = QAction("自动换行", self)
        wrap_action.setCheckable(True)
        wrap_action.setChecked(True)  # 默认启用
        wrap_action.triggered.connect(self.editor.toggle_wrap)
        view_menu.addAction(wrap_action)
        
        # 添加分割视图动作
        split_action = QAction("分割视图", self)
        split_action.setCheckable(True)
        split_action.setChecked(True)  # 默认启用
        split_action.triggered.connect(self.editor.toggle_split)
        view_menu.addAction(split_action)

    def toggle_preview_edit_mode(self, checked):
        """切换预览编辑模式"""
        self.editor.toggle_preview_edit_mode(checked)

    def toggle_toc_visible(self, checked):
        self.editor.set_toc_visible(checked)

def log_error(error_msg, level="INFO"):
    """记录错误到日志文件"""
    try:
        # 获取应用程序目录
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            
        # 确保目录存在
        os.makedirs(app_dir, exist_ok=True)
        
        # 使用时间戳创建日志文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(app_dir, f'error_{timestamp}.log')
        
        # 写入错误信息
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"级别: {level}\n")
            f.write(f"信息: {error_msg}\n")
            f.write(f"系统信息: {sys.platform}\n")
            f.write(f"Python版本: {sys.version}\n")
            if getattr(sys, 'frozen', False):
                f.write(f"运行模式: 打包模式\n")
                f.write(f"可执行文件: {sys.executable}\n")
                f.write(f"工作目录: {os.getcwd()}\n")
                f.write(f"环境变量: {dict(os.environ)}\n")
            else:
                f.write(f"运行模式: 开发模式\n")
                f.write(f"脚本路径: {__file__}\n")
    except Exception as e:
        print(f"写入日志失败: {str(e)}")

def setup_qt_environment():
    """设置 Qt 环境变量"""
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
        os.environ['QT_PLUGIN_PATH'] = os.path.join(app_dir, '_internal', 'PyQt6', 'Qt6', 'plugins')
        os.environ['QML2_IMPORT_PATH'] = os.path.join(app_dir, '_internal', 'PyQt6', 'Qt6', 'qml')
        QCoreApplication.addLibraryPath(os.path.join(app_dir, '_internal', 'PyQt6', 'Qt6', 'plugins'))

def main():
    if is_another_instance_running():
        sys.exit(0)
    setup_qt_environment()
    app = QApplication(sys.argv)
    window = MainWindow()
    create_single_instance_server(window)
    # 启动时带文件参数
    if len(sys.argv) > 1:
        file_path = os.path.abspath(sys.argv[1])
        if os.path.exists(file_path):
            window.editor.open_file(file_path)
            window.current_file_path = file_path
            window.is_dirty = False
            window.update_window_title()
            window.status_bar.showMessage(f'已打开文件: {file_path}')
            window.showNormal()
            window.activateWindow()
            window.raise_()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 