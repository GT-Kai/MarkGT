import sys
import os
import traceback
import datetime
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QMenuBar, QMenu, QFileDialog, QMessageBox, QToolBar, QStatusBar)
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QIcon, QAction
from editor import Editor

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
        # 创建工具栏
        toolbar = QToolBar("Markdown 工具栏")
        toolbar.setMovable(False)  # 禁止移动工具栏
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
        link_action.triggered.connect(lambda: self.insert_markdown("[", "](url)"))
        toolbar.addAction(link_action)

        image_action = QAction("图片", self)
        image_action.triggered.connect(lambda: self.insert_markdown("![", "](image_url)"))
        toolbar.addAction(image_action)

    def insert_markdown(self, prefix="", suffix=""):
        """在当前光标位置插入 Markdown 语法"""
        current_tab = self.editor.get_current_tab()
        if current_tab:
            editor = current_tab['editor']  # 这是 CustomEditor (QsciScintilla) 实例
            
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
                editor.insert(f"{prefix}")
            
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
            editor = current_tab['editor']  # 使用 editor 而不是 text_edit
            
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

    def process_markdown(self, text):
        """处理 Markdown 文本，确保表格和列表格式正确"""
        lines = text.split('\n')
        processed_lines = []
        in_table = False
        table_buffer = []

        for line in lines:
            # 检查是否是表格行
            if '|' in line and line.count('|') >= 2:
                in_table = True
                table_buffer.append(line)
            else:
                if in_table:
                    # 处理表格缓冲区
                    if table_buffer:
                        processed_lines.extend(table_buffer)
                        processed_lines.append('')  # 添加空行作为表格结束
                    table_buffer = []
                    in_table = False

                # 检查是否是列表项
                list_match = re.match(r'^(\s*)[*+-]\s+(.+)$', line)
                if list_match:
                    processed_lines.append(f'* {list_match.group(2)}')
                else:
                    processed_lines.append(line)

        # 处理最后的表格（如果有）
        if table_buffer:
            processed_lines.extend(table_buffer)
            processed_lines.append('')

        return '\n'.join(processed_lines)

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
        # 获取应用程序目录
        app_dir = os.path.dirname(sys.executable)
        # 设置插件路径
        os.environ['QT_PLUGIN_PATH'] = os.path.join(app_dir, '_internal', 'PyQt6', 'Qt6', 'plugins')
        os.environ['QML2_IMPORT_PATH'] = os.path.join(app_dir, '_internal', 'PyQt6', 'Qt6', 'qml')
        # 设置应用程序目录
        QCoreApplication.addLibraryPath(os.path.join(app_dir, '_internal', 'PyQt6', 'Qt6', 'plugins'))

def main():
    try:
        # 设置 Qt 环境
        setup_qt_environment()
        
        app = QApplication(sys.argv)
        window = MainWindow()
        
        # 处理命令行参数
        if len(sys.argv) > 1:
            try:
                # 获取第一个参数（文件路径）
                file_path = sys.argv[1]
                # 转换为绝对路径
                file_path = os.path.abspath(file_path)
                
                # 记录文件信息
                log_error(f"尝试打开文件: {file_path}", "DEBUG")
                
                # 检查文件是否存在
                if os.path.exists(file_path):
                    # 打开文件
                    if window.editor.open_file(file_path):
                        window.current_file_path = file_path
                        window.is_dirty = False
                        window.update_window_title()
                        window.status_bar.showMessage(f'已打开文件: {file_path}')
                        log_error(f"成功打开文件: {file_path}", "INFO")
                    else:
                        log_error(f"无法打开文件: {file_path}", "ERROR")
                else:
                    log_error(f"文件不存在: {file_path}", "ERROR")
            except Exception as e:
                error_msg = f"打开文件时出错: {str(e)}\n{traceback.format_exc()}"
                log_error(error_msg, "ERROR")
                QMessageBox.warning(window, '错误', f'打开文件时出错：{str(e)}')
        
        sys.exit(app.exec())
    except Exception as e:
        error_msg = f"程序运行出错: {str(e)}\n{traceback.format_exc()}"
        log_error(error_msg, "CRITICAL")
        QMessageBox.critical(None, '错误', f'程序运行出错：{str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    main() 