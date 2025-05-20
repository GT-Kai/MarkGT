from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QSplitter, QTextBrowser, 
                            QVBoxLayout, QTabWidget, QMenu, QFileDialog)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.Qsci import QsciScintilla, QsciLexerMarkdown
import mistune
from PyQt6.QtGui import QFont, QColor
import re
import os
from functools import partial

class CustomEditor(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_cursor_line = 0
        self._last_cursor_column = 0
        self._is_editing = False
        
    def keyPressEvent(self, event):
        # 记录按键前的光标位置
        self._last_cursor_line = self.getCursorPosition()[0]
        self._last_cursor_column = self.getCursorPosition()[1]
        self._is_editing = True
        super().keyPressEvent(event)
        
    def ensureCursorVisible(self):
        # 重写此方法以禁用自动滚动
        pass

class Editor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 不再需要创建自定义 markdown 解析器
        self.tabs = {}  # 初始化 tabs 字典
        self.init_ui()
        self.is_syncing = False
        self.last_line_count = 0
        self.is_editing = False
        self.current_file_path = None

    def init_ui(self):
        # 创建垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.tab_widget)

    def create_new_tab(self, file_path=None):
        # 创建新的标签页容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)

        # 创建水平布局用于编辑器和预览
        editor_layout = QHBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        tab_layout.addLayout(editor_layout)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        editor_layout.addWidget(splitter)

        # 创建编辑器
        editor = CustomEditor()
        
        # 设置编辑器字体
        font = QFont("Microsoft YaHei", 12)
        editor.setFont(font)
        
        # 设置语法高亮
        lexer = QsciLexerMarkdown()
        lexer.setFont(font)
        editor.setLexer(lexer)
        
        # 设置编辑器其他属性
        editor.setMarginWidth(0, 0)
        editor.setMarginWidth(1, 0)
        editor.setAutoIndent(True)
        editor.setIndentationGuides(True)
        editor.setIndentationsUseTabs(False)
        editor.setTabWidth(4)
        editor.setUtf8(True)
        editor.setMarginWidth(2, 0)
        editor.setMarginSensitivity(0, False)
        editor.setMarginSensitivity(1, False)
        editor.setMarginSensitivity(2, False)
        editor.setScrollWidth(1)
        editor.setScrollWidthTracking(True)
        editor.setWrapMode(QsciScintilla.WrapMode.WrapWord)
        editor.setMarginsBackgroundColor(QColor("#f0f0f0"))
        editor.setMarginsForegroundColor(QColor("#808080"))

        # 创建预览区域
        preview = QTextBrowser()
        preview.setOpenExternalLinks(True)
        preview.setFont(font)
        # 不再需要使用 setStyleSheet，样式将在 HTML 中设置
        # preview.setStyleSheet(self.get_preview_style())

        # 添加到分割器
        splitter.addWidget(editor)
        splitter.addWidget(preview)
        splitter.setSizes([600, 600])

        # 设置标签页标题
        if file_path:
            tab_title = os.path.basename(file_path)
        else:
            tab_title = "未命名"

        # 添加标签页
        tab_index = self.tab_widget.addTab(tab_container, tab_title)
        
        # 存储标签页信息
        self.tabs[tab_index] = {
            'container': tab_container,
            'editor': editor,
            'preview': preview,
            'splitter': splitter,
            'file_path': file_path
        }

        # 设置当前标签页
        self.tab_widget.setCurrentIndex(tab_index)

        # 连接信号
        self.setup_tab_connections(tab_index)

        # 如果是新文件，添加未保存标记
        if not file_path:
            self.update_tab_title(tab_index, True)

        return tab_index

    def setup_tab_connections(self, tab_index):
        tab_info = self.tabs[tab_index]
        editor = tab_info['editor']
        preview = tab_info['preview']

        # 使用 functools.partial 来创建信号连接
        from functools import partial

        # 连接编辑器的文本变化信号
        editor.textChanged.connect(partial(self.update_preview, tab_index))
        editor.textChanged.connect(partial(self.text_changed, tab_index))
        
        # 连接滚动信号
        editor.SCN_PAINTED.connect(partial(self.sync_editor_to_preview, tab_index))
        preview.verticalScrollBar().valueChanged.connect(partial(self.sync_preview_to_editor, tab_index))
        
        # 连接编辑器的鼠标滚轮事件
        editor.wheelEvent = lambda event: self.editor_wheel_event(event, tab_index)

    def editor_wheel_event(self, event, tab_index):
        # 用户主动滚动时，允许同步
        self.tabs[tab_index]['editor']._is_editing = False
        super(type(self.tabs[tab_index]['editor']), self.tabs[tab_index]['editor']).wheelEvent(event)

    def update_preview(self, tab_index):
        tab_info = self.tabs[tab_index]
        editor = tab_info['editor']
        preview = tab_info['preview']

        # 获取编辑器中的文本
        text = editor.text()

        # 处理Markdown文本
        processed_text = self.process_markdown(text)

        # 使用 mistune.html 渲染 Markdown
        html = mistune.html(processed_text)
        
        # 注释掉调试输出
        # print("Generated HTML:")
        # print(html)

        # 保存当前预览区域的滚动位置
        preview_scrollbar = preview.verticalScrollBar()
        scroll_ratio = preview_scrollbar.value() / max(1, preview_scrollbar.maximum())

        # 更新预览区域，但不触发同步
        self.is_syncing = True
        preview.setHtml(self.wrap_html_with_style(html))
        
        # 恢复预览区域的滚动位置
        if preview_scrollbar.maximum() > 0:
            new_position = int(scroll_ratio * preview_scrollbar.maximum())
            preview_scrollbar.setValue(new_position)
        
        self.is_syncing = False
        
    def wrap_html_with_style(self, html_content):
        """为 HTML 内容添加样式"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                margin: 0;
                padding: 15px;
                color: #333330;
            }}
            h1, h2, h3, h4, h5, h6 {{
                margin-top: 20px;
                margin-bottom: 15px;
            }}
            p {{
                margin: 10px 0;
                line-height: 1.6;
            }}
            code {{
                background-color: #f5f5f5;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: Consolas, monospace;
            }}
            pre {{
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                font-family: Consolas, monospace;
                overflow-x: auto;
            }}
            blockquote {{
                border-left: 4px solid #ddd;
                margin: 10px 0;
                padding-left: 15px;
                color: #666;
            }}
            /* 表格样式 */
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f5f5f5;
                font-weight: bold;
            }}
            /* 列表样式 - 减小缩进 */
            ol, ul {{
                margin: 0px 0;
                padding-left: 0px; /* 从20px减少到1px */
            }}
            li {{
                margin: 5px 0;
                padding-left: 0;
            }}
            /* 调整列表项内部内容 */
            li p {{
                margin: 0;
                padding: 0;
                display: inline;
            }}
            /* 图片样式 */
            img {{
                max-width: 100%;
                height: auto;
            }}
            /* 链接样式 */
            a {{
                color: #0066cc;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
        </head>
        <body>
        {html_content}
        </body>
        </html>
        """

    def sync_editor_to_preview(self, tab_index):
        # 添加安全检查
        if tab_index not in self.tabs:
            return
            
        if self.is_syncing or self.tabs[tab_index]['editor']._is_editing:
            return
            
        self.is_syncing = True
        try:
            editor = self.tabs[tab_index]['editor']
            preview = self.tabs[tab_index]['preview']

            # 获取编辑器当前可见区域的第一个可见行
            first_visible_line = editor.firstVisibleLine()
            total_lines = editor.lines()

            if total_lines > 0:
                 # 计算滚动比例
                 scroll_ratio = first_visible_line / total_lines

                 # 设置预览区域的滚动位置
                 preview_scrollbar = preview.verticalScrollBar()
                 preview_max = preview_scrollbar.maximum()
                 preview_visible_height = preview.viewport().height()
                 target_position = int(scroll_ratio * (preview_max + preview_visible_height))

                 # 确保滚动位置在有效范围内
                 target_position = max(0, min(target_position, preview_max))
                 preview_scrollbar.setValue(target_position)

        finally:
            self.is_syncing = False

    def sync_preview_to_editor(self, tab_index):
        # 添加安全检查
        if tab_index not in self.tabs:
            return
            
        if self.is_syncing or self.tabs[tab_index]['editor']._is_editing:
            return

        self.is_syncing = True
        try:
            editor = self.tabs[tab_index]['editor']
            preview = self.tabs[tab_index]['preview']

            # 获取预览区域的滚动信息
            preview_scrollbar = preview.verticalScrollBar()
            preview_scroll = preview_scrollbar.value()
            preview_max = preview_scrollbar.maximum()
            preview_visible_height = preview.viewport().height()

            if preview_max > 0:
                # 计算滚动比例
                scroll_ratio = preview_scroll / (preview_max + preview_visible_height)

                # 设置编辑器的滚动位置
                total_lines = editor.lines()
                target_line = int(scroll_ratio * total_lines)

                # 确保目标行在有效范围内
                target_line = max(0, min(target_line, total_lines))
                editor.setFirstVisibleLine(target_line)
        finally:
            self.is_syncing = False

    def process_markdown(self, text):
        """处理 Markdown 文本，确保表格和列表格式正确"""
        # 将文本按行分割
        lines = text.split('\n')
        processed_lines = []
        in_table = False
        in_list = False
        table_buffer = []

        for line in lines:
            # 检查是否是表格行
            if '|' in line:
                if not in_table:
                    in_table = True
                table_buffer.append(line)
                in_list = False  # 确保不在列表中
            else:
                if in_table:
                    # 处理表格缓冲区
                    if table_buffer:
                        # 确保表格行之间有正确的分隔
                        processed_lines.extend(table_buffer)
                        processed_lines.append('')  # 添加空行作为表格结束
                    table_buffer = []
                    in_table = False

                # 检查是否是列表项
                list_match = re.match(r'^(\s*)[*+-]\s+(.+)$', line)
                if list_match:
                    # 移除所有缩进，只保留一个空格
                    processed_lines.append(f'* {list_match.group(2)}')
                    in_list = True
                else:
                    # 如果不是列表项，保持原样
                    processed_lines.append(line)
                    in_list = False

        # 处理最后的表格（如果有）
        if table_buffer:
            processed_lines.extend(table_buffer)
            processed_lines.append('')

        return '\n'.join(processed_lines)

    def close_tab(self, index):
        if index in self.tabs:
            # 断开所有信号连接
            tab_info = self.tabs[index]
            editor = tab_info['editor']
            preview = tab_info['preview']
            
            try:
                editor.textChanged.disconnect()
                editor.SCN_PAINTED.disconnect()
                preview.verticalScrollBar().valueChanged.disconnect()
            except:
                pass  # 忽略断开连接时的错误
            
            # 移除标签页
            self.tab_widget.removeTab(index)
            # 清理标签页信息
            del self.tabs[index]
            # 重新映射剩余标签页的索引
            self.remap_tab_indices()
            # 重新连接所有标签页的信号
            for new_index in self.tabs:
                self.setup_tab_connections(new_index)

    def remap_tab_indices(self):
        # 创建新的标签页信息字典
        new_tabs = {}
        for i in range(self.tab_widget.count()):
            # 获取当前标签页的容器
            container = self.tab_widget.widget(i)
            # 找到对应的旧索引
            old_index = None
            for idx, tab_info in self.tabs.items():
                if tab_info['container'] == container:
                    old_index = idx
                    break
            if old_index is not None:
                new_tabs[i] = self.tabs[old_index]
        self.tabs = new_tabs

    def open_file(self, file_path):
        try:
            # 检查文件是否已经打开
            for tab_index, tab_info in self.tabs.items():
                if tab_info['file_path'] == file_path:
                    # 如果文件已经打开，切换到对应的标签页
                    self.tab_widget.setCurrentIndex(tab_index)
                    return True

            # 检查文件是否存在
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                return False

            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                print(f"文件太大: {file_path}")
                return False

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 如果 UTF-8 解码失败，尝试其他编码
                try:
                    with open(file_path, 'r', encoding='gbk') as f:
                        content = f.read()
                except:
                    print(f"无法读取文件: {file_path}")
                    return False
            
            # 创建新标签页
            tab_index = self.create_new_tab(file_path)
            
            # 设置编辑器内容
            self.tabs[tab_index]['editor'].setText(content)
            
            return True
        except Exception as e:
            print(f"打开文件失败: {str(e)}")
            return False

    def text_changed(self, tab_index):
        # 更新标签页标题
        self.update_tab_title(tab_index, True)
        # 发送信号通知主窗口文本已修改
        if hasattr(self.parent(), 'document_modified'):
            self.parent().document_modified()

    def update_tab_title(self, tab_index, is_modified=False):
        if tab_index in self.tabs:
            tab_info = self.tabs[tab_index]
            if tab_info['file_path']:
                file_name = os.path.basename(tab_info['file_path'])
            else:
                file_name = "未命名"
            
            # 添加未保存标记
            if is_modified:
                title = f"{file_name}*"
            else:
                title = file_name
                
            self.tab_widget.setTabText(tab_index, title)

    def save_file(self, tab_index):
        tab_info = self.tabs[tab_index]
        if not tab_info['file_path']:
            return self.save_file_as(tab_index)
        
        try:
            # 获取文本并处理换行符
            text = tab_info['editor'].text()
            # 移除多余的换行符
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            # 确保文件末尾只有一个换行符
            text = text.rstrip('\n') + '\n'
            
            with open(tab_info['file_path'], 'w', encoding='utf-8') as f:
                f.write(text)
            # 更新标签页标题，移除未保存标记
            self.update_tab_title(tab_index, False)
            return True
        except Exception as e:
            print(f"保存文件失败: {str(e)}")
            return False

    def save_file_as(self, tab_index):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存文件",
            "",
            "Markdown Files (*.md);;All Files (*.*)"
        )
        
        if file_path:
            try:
                # 获取文本并处理换行符
                text = self.tabs[tab_index]['editor'].text()
                # 移除多余的换行符
                text = text.replace('\r\n', '\n').replace('\r', '\n')
                # 确保文件末尾只有一个换行符
                text = text.rstrip('\n') + '\n'
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                # 更新标签页信息
                self.tabs[tab_index]['file_path'] = file_path
                # 更新标签页标题，移除未保存标记
                self.update_tab_title(tab_index, False)
                return True
            except Exception as e:
                print(f"保存文件失败: {str(e)}")
                return False
        return False

    def setup_connections(self):
        # 这个方法现在不需要做任何事情，因为每个标签页的连接都在 create_new_tab 中设置
        pass 

    def toggle_wrap(self, checked):
        # 获取当前标签页的编辑器
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            editor = self.tabs[current_index]['editor']
            if checked:
                editor.setWrapMode(QsciScintilla.WrapMode.WrapWord)
            else:
                editor.setWrapMode(QsciScintilla.WrapMode.WrapNone)

    def toggle_split(self, checked):
        # 获取当前标签页的分割器和预览区域
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            splitter = self.tabs[current_index]['splitter']
            preview = self.tabs[current_index]['preview']
            if checked:
                preview.show()
                splitter.setSizes([600, 600])
            else:
                preview.hide()
                splitter.setSizes([1200, 0])

    def get_current_tab(self):
        """获取当前标签页的信息"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0 and current_index in self.tabs:
            return self.tabs[current_index]
        return None 