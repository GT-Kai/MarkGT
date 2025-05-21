from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QSplitter, QTextBrowser, 
                            QVBoxLayout, QTabWidget, QMenu, QFileDialog, QListWidget, QListWidgetItem)
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
        
    def linesOnScreen(self):
        """返回当前可见的行数"""
        # 获取可见区域高度
        visible_height = self.height()
        # 获取行高
        line_height = self.textHeight(0)  # 使用第0行作为参考
        
        # 计算可见行数
        if line_height > 0:
            return visible_height // line_height
        return 20  # 默认值，如果无法计算

class CustomListRenderer(mistune.HTMLRenderer):
    def list(self, text, ordered, depth, start=None, raw=None):
        """Render list and add custom class for styling."""
        style = 'margin:0;padding:0;text-indent:0;'
        if ordered:
            return f'<ol style="{style}">{text}</ol>\n'
        else:
            return f'<ul style="{style}">{text}</ul>\n'

    def list_item(self, text, level=0):
        """Render list item."""
        # 处理任务列表项
        task_match = re.match(r'^\[([ xX])\]\s+(.+)$', text.strip())
        if task_match:
            checked = task_match.group(1).lower() == 'x'
            content = task_match.group(2)
            
            # 使用更大更清晰的复选框
            checkbox_text = "☑" if checked else "☐"
            toggle_url = f"pyqt://task-toggle/{'unchecked' if checked else 'checked'}"
            
            # 更大、更明显的点击区域，使用带边框的设计
            checkbox_style = (
                "text-decoration:none;"
                "font-size:18px;" # 稍微减小字体大小
                f"color:{('#4285f4' if checked else '#616161')};"
                "margin-right:8px;" # 减小右边距
                "padding:2px 4px;" # 减小内边距
                "border-radius:3px;" # 减小圆角
                "cursor:pointer;"
                f"background-color:{('rgba(66,133,244,0.1)' if checked else 'transparent')};"
            )
            checkbox = f'<a href="{toggle_url}" style="{checkbox_style}">{checkbox_text}</a>'
            
            # 返回更紧凑的列表项样式
            return f'<li style="margin:2px 0;padding:1px 0;text-indent:0;margin-left:-10px;list-style-type:none;line-height:1.3;">{checkbox} {content}</li>\n'
            
        # 如果 text 以数字.数字.数字 开头，我们保留它
        m = re.match(r'^((?:\d+\.)+\d+)\s+(.+)', text.strip())
        if m:
             # 保留原始编号和文本
            content = f'{m.group(1)} {m.group(2)}'
        else:
            content = text.strip() # 移除可能的尾随换行

        # 返回带有内容的列表项 HTML - 添加行高控制
        return f'<li style="margin:0;padding:0;text-indent:0;margin-left:-8px;line-height:1.3;">{content}</li>\n'

    def table(self, text):
        """渲染表格"""
        return f'<table>{text}</table>\n'
    
    def table_head(self, text):
        """渲染表头"""
        return f'<tr>{text}</tr>\n'
    
    def table_body(self, text):
        """渲染表体"""
        return text
    
    def table_row(self, text):
        """渲染表格行"""
        return f'<tr>{text}</tr>\n'
    
    def table_cell(self, text, align=None, head=False):
        """渲染表格单元格"""
        tag = 'th' if head else 'td'
        if align:
            return f'<{tag} style="text-align:{align}">{text}</{tag}>\n'
        return f'<{tag}>{text}</{tag}>\n'

    def block_code(self, code, info=None):
        # 用table模拟代码块卡片，兼容性最好
        style = (
            "background:#f6f8fa;"
            "border:1px solid #d0d0d0;"
            "padding:6px 10px;"
            "font-family:Microsoft YaHei,微软雅黑,Consolas,monospace;"
            "font-size:14px;"
            "white-space:pre;"
            "line-height: 1.0;"
        )
        return (
            f'<table width="100%" cellspacing="0" cellpadding="0" style="margin:12px 0;"><tr>'
            f'<td style="{style}">{mistune.escape(code)}</td>'
            f'</tr></table>'
        )

class Editor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabs = {}
        self.init_ui()
        self.is_syncing = False
        self.last_line_count = 0
        self.is_editing = False
        self.current_file_path = None
        self.preview_edit_mode = False
        self.toc_widgets = {}  # 记录每个tab的目录控件
        
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧目录区
        self.toc_list = QListWidget()
        self.toc_list.setMaximumWidth(260)
        self.toc_list.itemClicked.connect(self.on_toc_item_clicked)
        font = QFont("Microsoft YaHei", 11)
        self.toc_list.setFont(font)
        main_layout.addWidget(self.toc_list)

        # 右侧主区（原有垂直布局）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        right_layout.addWidget(self.tab_widget)
        main_layout.addWidget(right_widget)

    def create_new_tab(self, file_path=None):
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
        preview.setAcceptRichText(False)
        preview.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)
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
        self.toc_widgets[tab_index] = []  # 记录每个tab的目录项
        self.tab_widget.setCurrentIndex(tab_index)
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
        
        # 简化滚动逻辑：只用SCN_PAINTED事件触发简单同步
        editor.SCN_PAINTED.connect(partial(self.sync_editor_to_preview_smart, tab_index))
        # 删除预览滚动条对编辑器的影响
        # preview.verticalScrollBar().valueChanged.connect(partial(self.sync_preview_to_editor, tab_index))
        
        # 连接编辑器的鼠标滚轮事件
        editor.wheelEvent = lambda event: self.editor_wheel_event(event, tab_index)

        # 连接预览区域的文本变化信号
        preview.textChanged.connect(partial(self.preview_text_changed, tab_index))
        
        # 设置预览区域的上下文菜单策略
        preview.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        preview.customContextMenuRequested.connect(partial(self.show_preview_context_menu, tab_index))
        
        # 设置URL处理函数，用于处理任务列表更新
        preview.setOpenLinks(False)  # 禁用自动打开链接
        preview.anchorClicked.connect(partial(self.handle_url_clicked, tab_index))

    def handle_url_clicked(self, tab_index, url):
        """处理预览区URL点击事件，特别用于任务列表状态更新"""
        url_str = url.toString()
        
        # 处理任务列表更新 - 新版本链接格式
        if url_str.startswith("pyqt://task-toggle/"):
            try:
                current_tab = self.get_current_tab()
                if not current_tab:
                    return
                    
                editor = current_tab['editor']
                preview = current_tab['preview']
                
                # 获取当前鼠标位置附近文本
                cursor = preview.textCursor()
                cursor.select(cursor.SelectionType.LineUnderCursor)
                line_text = cursor.selectedText()
                
                # 查找当前编辑的是哪个任务
                is_checked = "checked" in url_str
                
                # 从预览内容提取任务文本 - 更宽松的匹配
                match = re.search(r'[☐☑]\s+(.+)$', line_text)
                if match:
                    task_content = match.group(1).strip()
                    
                    # 移除HTML标签，简化匹配
                    clean_content = re.sub(r'<[^>]+>', '', task_content)
                    
                    # 在编辑器中找到并更新对应任务
                    text = editor.text()
                    lines = text.split('\n')
                    
                    # 日志输出便于调试
                    print(f"任务内容: '{clean_content}'")
                    
                    # 为包含格式的文本做特殊处理
                    # 移除常见的Markdown格式化字符
                    plain_content = re.sub(r'[*_`~]|(https?://\S+)|\[[^\]]+\]\([^)]+\)', '', clean_content)
                    plain_content = re.sub(r'\s+', ' ', plain_content).strip()
                    
                    # 记录最佳匹配
                    best_match_idx = -1
                    best_similarity = 0
                    
                    # 逐行检查任务项
                    for i, line in enumerate(lines):
                        # 首先检查是否为任务列表项
                        task_match = re.match(r'^(\s*)-\s*\[([ xX])\]\s+(.+)$', line)
                        if task_match:
                            indent = task_match.group(1)
                            status = task_match.group(2)
                            original_content = task_match.group(3)
                            print(f"检查行 {i+1}: '{original_content}'")
                            
                            # 对Markdown源代码也进行格式清理
                            plain_original = re.sub(r'[*_`~]|(https?://\S+)|\[[^\]]+\]\([^)]+\)', '', original_content)
                            plain_original = re.sub(r'\s+', ' ', plain_original).strip()
                            
                            # 检查内容是否相似 - 使用关键字匹配而非完全匹配
                            # 1. 检查纯文本是否包含关系
                            if plain_content and plain_original and (plain_content in plain_original or plain_original in plain_content):
                                similarity = 0.9
                            else:
                                # 2. 拆分内容为单词，计算关键词匹配程度
                                content_words = re.findall(r'\w+', clean_content.lower())
                                line_words = re.findall(r'\w+', original_content.lower())
                                
                                # 计算内容相似度
                                common_words = [w for w in content_words if w in line_words]
                                if content_words and line_words:
                                    similarity = len(common_words) / max(1, min(len(content_words), len(line_words)))
                                else:
                                    similarity = 0
                            
                            print(f"相似度: {similarity}")
                            
                            # 更新最佳匹配
                            if similarity > best_similarity:
                                best_similarity = similarity
                                best_match_idx = i
                    
                    # 如果找到匹配度足够高的任务，进行更新
                    if best_match_idx >= 0 and best_similarity > 0.4:
                        print(f"找到最佳匹配的任务行: {best_match_idx+1}, 相似度: {best_similarity}")
                        line = lines[best_match_idx]
                        # 更新任务状态
                        if is_checked:
                            new_line = re.sub(r'(\s*-\s*\[)[ ](\])', r'\1x\2', line)
                        else:
                            new_line = re.sub(r'(\s*-\s*\[)[xX](\])', r'\1 \2', line)
                        
                        # 如果行内容发生变化，更新编辑器
                        if new_line != line:
                            lines[best_match_idx] = new_line
                            new_text = '\n'.join(lines)
                            
                            # 临时阻断信号，防止更新循环
                            try:
                                editor.blockSignals(True)
                                editor.setText(new_text)
                            finally:
                                editor.blockSignals(False)
                            
                            # 手动触发预览更新
                            self.update_preview(tab_index)
            except Exception as e:
                print(f"处理任务状态更新出错: {str(e)}")

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
        renderer = CustomListRenderer()
        markdown = mistune.create_markdown(renderer=renderer, plugins=['table'])
        html = markdown(processed_text)
        
        # 添加自定义样式处理
        # html = html.replace('<li>', '<li style="margin: 0; padding: 0; line-height: 1.2;">')
        # html = html.replace('<li><p>', '<li style="margin: 0; padding: 0; line-height: 1.2;"><p style="margin: 0; padding: 0; line-height: 1;">')
        
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
        self.update_toc(tab_index)
        
    def wrap_html_with_style(self, html_content):
        """为 HTML 内容添加样式"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            /* 列表样式 */
            ul, ol {{
                margin: 0.3em 0 !important;
                padding-left: 0 !important;
                margin-right: 0 !important;
                padding-right: 0 !important;
                text-indent: 0 !important;
            }}

            li {{
                margin: 0 !important; /* 从1px减小到0 */
                padding: 0 !important;
                line-height: 1.2 !important; /* 从1.3减小到1.2 */
            }}
            
            /* 解决嵌套列表问题 */
            li > ul, li > ol {{
                margin: 0 0 0 12px !important; /* 减小左边距从16px到12px */
                padding: 0 !important;
            }}
            
            /* 确保链接显示正常 */
            li a {{
                display: inline-block;
                vertical-align: middle;
            }}
            
            /* 任务列表特殊样式 */
            li a[href^="pyqt://task-toggle/"] {{
                display: inline-block;
                text-align: center;
                vertical-align: middle;
                line-height: 1;
                border-radius: 3px;
                cursor: pointer;
                transition: all 0.15s ease-in-out;
            }}
            
            li a[href^="pyqt://task-toggle/"]:hover {{
                background-color: rgba(66, 133, 244, 0.15) !important;
                transform: scale(1.03);
            }}
            
            /* 优化标题间距 */
            h1, h2, h3, h4, h5, h6 {{
                margin-top: 20px;
                margin-bottom: 12px;
                font-weight: 600;
                line-height: 1.2;
            }}
            
            body {{
                font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;
                margin: 0;
                padding: 20px;
                color: #333;
                line-height: 1.35;
                max-width: 900px;
                margin: 0 auto;
            }}
            h1, h2, h3, h4, h5, h6 {{
                margin-top: 20px;
                margin-bottom: 12px;
                font-weight: 600;
                line-height: 1.2;
            }}
            h1 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
            h2 {{ font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
            h3 {{ font-size: 1.25em; }}
            h4 {{ font-size: 1em; }}
            h5 {{ font-size: 0.875em; }}
            h6 {{ font-size: 0.85em; color: #6a737d; }}
            
            p {{
                margin: 8px 0;
                line-height: 1.25;
            }}
            
            /* 行内代码样式 */
            code {{
                font-family: 'Microsoft YaHei', '微软雅黑', Consolas, Monaco, 'Andale Mono', monospace;
                background-color: #f6f8fa;
                padding: 0.2em 0.4em;
                border-radius: 3px;
                font-size: 14px;
                color: #c7254e;
                /* font-weight: bold; */
            }}
            
            /* 代码块样式 */
            pre {{
                font-family: 'Microsoft YaHei', '微软雅黑', Consolas, Monaco, 'Andale Mono', monospace;
                background-color: #f6f8fa;
                padding: 12px; /* 从16px减小到12px */
                border-radius: 4px; /* 从6px减小到4px */
                overflow-x: auto;
                line-height: 1.0;
                margin: 12px 0; /* 从16px减小到12px */
                font-size: 14px;
                /* font-weight: bold; */
                border: 1px solid #d0d0d0; /* 从1.5px减小到1px */
                box-shadow: 0 1px 4px 0 rgba(0,0,0,0.03); /* 减小阴影 */
            }}
            
            pre code {{
                background-color: transparent;
                padding: 0;
                border-radius: 0;
                font-size: 14px;
                color: #c7254e;
                /* font-weight: bold; */
            }}
            
            blockquote {{
                margin: 12px 0; /* 从16px减小到12px */
                padding: 0 0.8em; /* 从1em减小到0.8em */
                color: #6a737d;
                border-left: 0.25em solid #dfe2e5;
                line-height: 1.3; /* 添加引用块行高控制 */
            }}
            
            /* 表格样式 */
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 12px 0; /* 从16px减小到12px */
                overflow: auto;
            }}
            
            th, td {{
                padding: 5px 10px; /* 从6px 13px减小 */
                border: 1px solid #dfe2e5;
                line-height: 1.25; /* 添加表格行高控制 */
            }}
            
            th {{
                background-color: #f6f8fa;
                font-weight: 600;
            }}
            
            tr:nth-child(2n) {{
                background-color: #f6f8fa;
            }}
            
            li {{
                margin-left: 0 !important;
                padding-left: 0 !important;
            }}
            
            li p {{
                margin: 0;
                padding: 0;
                line-height: 1; /* 列表中的段落，设置更小的行高 */
            }}
            
            li + li {{
                margin-top: 0;
            }}
            
            /* 图片样式 */
            img {{
                max-width: 100%;
                box-sizing: border-box;
                margin: 12px 0; /* 从16px减小到12px */
            }}
            
            /* 链接样式 */
            a {{
                color: #0366d6;
                text-decoration: none;
            }}
            
            a:hover {{
                text-decoration: underline;
            }}
            
            /* 水平线样式 */
            hr {{
                height: 0.2em; /* 从0.25em减小到0.2em */
                padding: 0;
                margin: 20px 0; /* 从24px减小到20px */
                background-color: #e1e4e8;
                border: 0;
            }}
        </style>
        <script>
            function toggleTaskStatus(checkbox) {{
                // 获取复选框的状态
                const isChecked = checkbox.checked;
                // 获取所在的列表项
                const listItem = checkbox.parentNode;
                const listIndex = Array.from(document.querySelectorAll('li')).indexOf(listItem);
                
                // 构建事件数据，将传递给Python
                const eventData = {{
                    "type": "taskToggle",
                    "index": listIndex,
                    "checked": isChecked
                }};
                
                // 使用QWebChannel发送消息到Python
                // 这里使用了自定义的URL scheme来模拟消息传递
                window.location.href = "pyqt://task-toggle/" + JSON.stringify(eventData);
            }}
        </script>
        </head>
        <body>{html_content}</body>
        </html>
        """

    def sync_editor_to_preview_smart(self, tab_index):
        """智能内容锚定对齐：优先锚定编辑区首行和中间行内容，在预览区查找并滚动到对应位置，找不到则退回比例映射。"""
        if tab_index not in self.tabs or self.is_syncing:
            return
        self.is_syncing = True
        try:
            editor = self.tabs[tab_index]['editor']
            preview = self.tabs[tab_index]['preview']
            first_line = editor.firstVisibleLine()
            visible_lines = editor.linesOnScreen()
            last_line = min(first_line + visible_lines - 1, editor.lines() - 1)
            text_lines = editor.text().split('\n')
            if not text_lines:
                return
            # 取首行和中间行内容
            anchor_lines = []
            if first_line < len(text_lines):
                anchor_lines.append(text_lines[first_line].strip())
            if visible_lines > 2:
                mid_line = first_line + visible_lines // 2
                if mid_line < len(text_lines):
                    anchor_lines.append(text_lines[mid_line].strip())
            # 内容清洗，去除多余空格和格式符号
            def clean_line(line):
                line = re.sub(r'^#+\s*', '', line)  # 去除标题符号
                line = re.sub(r'^[-*+]\s*', '', line)  # 去除无序列表符号
                line = re.sub(r'^\d+\.\s*', '', line)  # 去除有序列表符号
                line = re.sub(r'^>\s*', '', line)  # 去除引用符号
                line = re.sub(r'^```.*', '', line)  # 去除代码块标记
                return line.strip()
            anchor_lines = [clean_line(l) for l in anchor_lines if l and len(l.strip()) > 2]
            # 在预览区查找这些内容
            preview_text = preview.toPlainText()
            found_pos = -1
            for anchor in anchor_lines:
                if not anchor or len(anchor) < 3:
                    continue
                found_pos = preview_text.find(anchor)
                if found_pos != -1:
                    break
            # 滚动预览区
            if found_pos != -1:
                ratio = found_pos / max(1, len(preview_text))
                scrollbar = preview.verticalScrollBar()
                target = int(ratio * scrollbar.maximum())
                scrollbar.setValue(target)
            else:
                # 找不到时退回比例映射
                self.sync_editor_to_preview(tab_index)
        finally:
            self.is_syncing = False

    def process_markdown(self, text):
        """处理 Markdown 文本，确保表格和列表格式正确"""
        lines = text.split('\n')
        processed_lines = []
        in_table = False
        table_buffer = []

        for line in lines:
            # 检查是否是表格行（包含 | 且不是空行）
            if '|' in line and line.strip():
                if not in_table:
                    in_table = True
                table_buffer.append(line)
            else:
                if in_table:
                    # 如果之前在表格里，并且当前行不是表格行，处理并清空表格缓冲区
                    if table_buffer:
                        # 确保表格有分隔行
                        if len(table_buffer) == 1:
                            # 如果只有一行，添加分隔行
                            header = table_buffer[0]
                            separator = '|' + '|'.join(['---' for _ in header.split('|')[1:-1]]) + '|'
                            table_buffer.append(separator)
                        processed_lines.extend(table_buffer)
                        processed_lines.append('')  # 表格后加空行
                    table_buffer = []
                    in_table = False

                # 检查是否是多级编号（如 1.1、1.2.3、2.3.4.5）
                m = re.match(r'^((?:\d+\.)+\d+)\s+(.+)', line)
                if m:
                    # 计算缩进级别
                    level = m.group(1).count('.')
                    indent = '  ' * level  # 每级2个空格
                    processed_lines.append(f'{indent}{m.group(1)}. {m.group(2)}')
                    continue
                    
                # 检查是否是任务列表项
                task_match = re.match(r'^(\s*)-\s*\[([ xX])\]\s+(.+)$', line)
                if task_match:
                    indent = task_match.group(1)
                    status = task_match.group(2)
                    content = task_match.group(3)
                    processed_lines.append(f'{indent}- [{status}] {content}')
                    continue

                # 检查是否是无序列表项
                list_match = re.match(r'^(\s*)[*+-]\s+(.+)$', line)
                if list_match:
                    indent = list_match.group(1)
                    content = list_match.group(2)
                    processed_lines.append(f'{indent}* {content}')
                else:
                    processed_lines.append(line)

        # 如果文本以表格结束，处理剩余的表格缓冲区
        if in_table and table_buffer:
            if len(table_buffer) == 1:
                # 如果只有一行，添加分隔行
                header = table_buffer[0]
                separator = '|' + '|'.join(['---' for _ in header.split('|')[1:-1]]) + '|'
                table_buffer.append(separator)
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
            
            # 确保初始状态为已保存
            self.update_tab_title(tab_index, False)
            
            return True
        except Exception as e:
            print(f"打开文件失败: {str(e)}")
            return False

    def text_changed(self, tab_index):
        # 更新标签页标题
        self.update_tab_title(tab_index, True)
        self.update_toc(tab_index)
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

    def preview_text_changed(self, tab_index):
        """处理预览区域的文本变化"""
        if not self.preview_edit_mode or tab_index not in self.tabs:
            return
        try:
            tab_info = self.tabs[tab_index]
            preview = tab_info['preview']
            editor = tab_info['editor']

            preview_text = preview.toPlainText()
            # 防止递归：只有内容变化时才setText
            if editor.text() != preview_text:
                # 临时断开信号，防止递归
                try:
                    editor.blockSignals(True)
                    self.is_syncing = True
                    editor.setText(preview_text)
                finally:
                    self.is_syncing = False
                    editor.blockSignals(False)
            self.update_tab_title(tab_index, True)
            window = self.window()
            if hasattr(window, 'document_modified'):
                window.document_modified()
        except Exception as e:
            self.is_syncing = False
            print(f"预览编辑出错: {str(e)}")

    def toggle_preview_edit_mode(self, checked):
        """切换预览编辑模式"""
        self.preview_edit_mode = checked
        current_tab = self.get_current_tab()
        if current_tab:
            preview = current_tab['preview']
            editor = current_tab['editor']
            
            if checked:
                # 进入预览编辑模式
                preview.setReadOnly(False)
                editor.hide()
                # 使用原始Markdown文本而非HTML
                markdown_text = editor.text()
                preview.setPlainText(markdown_text)
                # 设置适合编辑的样式
                preview.setStyleSheet("""
                    QTextBrowser {
                        font-family: 'Microsoft YaHei', sans-serif;
                        font-size: 12pt;
                        line-height: 1.6;
                        background-color: #fafafa;
                        color: #333;
                        border: none;
                        padding: 10px;
                    }
                """)
            else:
                # 退出预览编辑模式
                preview.setReadOnly(True)
                editor.show()
                # 更新编辑器内容
                editor.setText(preview.toPlainText())
                # 清除编辑样式
                preview.setStyleSheet("")
                # 重新渲染Markdown
                self.update_preview(self.tab_widget.currentIndex())

    def get_current_editor(self):
        """获取当前活动的编辑器（可能是编辑器或预览区域）"""
        current_tab = self.get_current_tab()
        if current_tab:
            if self.preview_edit_mode:
                return current_tab['preview']
            else:
                return current_tab['editor']
        return None

    def get_current_text(self):
        """获取当前编辑器的文本内容"""
        editor = self.get_current_editor()
        if editor:
            if isinstance(editor, QTextBrowser):
                return editor.toPlainText()
            else:
                return editor.text()
        return ""

    def set_current_text(self, text):
        """设置当前编辑器的文本内容"""
        editor = self.get_current_editor()
        if editor:
            if isinstance(editor, QTextBrowser):
                editor.setPlainText(text)
            else:
                editor.setText(text) 

    def show_preview_context_menu(self, tab_index, position):
        """显示预览区域的右键菜单"""
        if not self.preview_edit_mode:
            return
            
        tab_info = self.tabs[tab_index]
        preview = tab_info['preview']
        
        menu = QMenu()
        
        # 添加常用的Markdown格式选项
        h1_action = menu.addAction("标题 1")
        h1_action.triggered.connect(lambda: self.insert_markdown_in_preview(preview, "# "))
        
        h2_action = menu.addAction("标题 2")
        h2_action.triggered.connect(lambda: self.insert_markdown_in_preview(preview, "## "))
        
        h3_action = menu.addAction("标题 3")
        h3_action.triggered.connect(lambda: self.insert_markdown_in_preview(preview, "### "))
        
        menu.addSeparator()
        
        bold_action = menu.addAction("粗体")
        bold_action.triggered.connect(lambda: self.insert_markdown_in_preview(preview, "**", "**"))
        
        italic_action = menu.addAction("斜体")
        italic_action.triggered.connect(lambda: self.insert_markdown_in_preview(preview, "*", "*"))
        
        menu.addSeparator()
        
        bullet_list_action = menu.addAction("无序列表")
        bullet_list_action.triggered.connect(lambda: self.insert_markdown_in_preview(preview, "- "))
        
        number_list_action = menu.addAction("有序列表")
        number_list_action.triggered.connect(lambda: self.insert_markdown_in_preview(preview, "1. "))
        
        menu.addSeparator()
        
        code_action = menu.addAction("代码块")
        code_action.triggered.connect(lambda: self.insert_markdown_in_preview(preview, "```\n", "\n```"))
        
        inline_code_action = menu.addAction("行内代码")
        inline_code_action.triggered.connect(lambda: self.insert_markdown_in_preview(preview, "`", "`"))
        
        menu.exec(preview.mapToGlobal(position))
        
    def insert_markdown_in_preview(self, preview, prefix, suffix=""):
        """在预览区域插入Markdown格式文本"""
        cursor = preview.textCursor()
        selected_text = cursor.selectedText()
        
        if selected_text:
            cursor.insertText(f"{prefix}{selected_text}{suffix}")
        else:
            cursor.insertText(prefix + suffix)
            if suffix:
                # 如果有后缀，将光标放在前缀和后缀之间
                pos = cursor.position()
                cursor.setPosition(pos - len(suffix))
                preview.setTextCursor(cursor) 

    def update_toc(self, tab_index):
        """解析当前tab的标题并更新目录，跳过代码块内容"""
        if tab_index not in self.tabs:
            return
        editor = self.tabs[tab_index]['editor']
        text = editor.text()
        lines = text.split('\n')
        self.toc_list.clear()
        toc_items = []
        in_code_block = False
        for i, line in enumerate(lines):
            # 检查代码块开关
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            m = re.match(r'^(#{1,6})\s+(.+)', line)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
                item = QListWidgetItem('  ' * (level-1) + title)
                item.setData(Qt.ItemDataRole.UserRole, i)
                self.toc_list.addItem(item)
                toc_items.append((i, title, level))
        self.toc_widgets[tab_index] = toc_items

    def on_toc_item_clicked(self, item):
        """点击目录项跳转到对应行"""
        line = item.data(Qt.ItemDataRole.UserRole)
        current_tab = self.get_current_tab()
        if current_tab:
            editor = current_tab['editor']
            editor.setCursorPosition(line, 0)
            editor.setFocus() 

    def set_toc_visible(self, visible: bool):
        """控制目录栏的显示与隐藏"""
        self.toc_list.setVisible(visible) 

    def analyze_document_structure(self, text):
        """分析文档结构，识别标题、列表、代码块等元素的位置"""
        lines = text.split('\n')
        structure = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            # 检测行的类型
            line_type = "text"  # 默认为普通文本
            importance = 0  # 元素重要性，用于优先级排序
            
            # 检查代码块开关
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                line_type = "code_fence"
                importance = 80
            elif in_code_block:
                line_type = "code_content"
                importance = 40
            # 检查标题
            elif re.match(r'^#{1,6}\s+.+', line):
                level = len(re.match(r'^(#{1,6})', line).group(1))
                line_type = f"h{level}"
                importance = 100 - level * 5  # h1最重要，然后是h2，依此类推
            # 检查任务列表
            elif re.match(r'^\s*-\s*\[[ xX]\]\s+.+', line):
                line_type = "task_item"
                importance = 70
            # 检查普通列表
            elif re.match(r'^\s*[-*+]\s+.+', line):
                line_type = "list_item"
                importance = 60
            # 检查有序列表
            elif re.match(r'^\s*\d+\.\s+.+', line):
                line_type = "ordered_item"
                importance = 65
            # 检查表格
            elif '|' in line and re.match(r'^[\s|:-]*$', line.strip()):
                line_type = "table_separator"
                importance = 75
            elif '|' in line and not line.strip().startswith('|'):
                line_type = "table_content"
                importance = 73
            # 检查引用块
            elif line.strip().startswith('>'):
                line_type = "blockquote"
                importance = 55
            # 检查水平线
            elif re.match(r'^-{3,}$|^_{3,}$|^\*{3,}$', line.strip()):
                line_type = "hr"
                importance = 50
            # 检查图片
            elif re.search(r'!\[.*\]\(.*\)', line):
                line_type = "image"
                importance = 85
            # 检查链接
            elif re.search(r'\[.*\]\(.*\)', line):
                line_type = "link"
                importance = 45
            
            # 记录行的结构信息
            structure.append({
                'line': i,
                'content': line,
                'type': line_type,
                'importance': importance
            })
        
        return structure
        
    def find_matching_elements(self, editor_line, document_structure):
        """找到编辑器中某一行在预览中对应的元素"""
        if not document_structure or editor_line >= len(document_structure):
            return None
            
        # 获取目标行的类型
        target_element = document_structure[editor_line]
        target_type = target_element['type']
        
        # 如果是重要元素，直接返回
        if target_element['importance'] >= 70:
            return target_element
            
        # 向上搜索最近的重要元素
        prev_important = None
        for i in range(editor_line, -1, -1):
            if document_structure[i]['importance'] >= 70:
                prev_important = document_structure[i]
                break
                
        # 向下搜索最近的重要元素
        next_important = None
        for i in range(editor_line + 1, len(document_structure)):
            if document_structure[i]['importance'] >= 70:
                next_important = document_structure[i]
                break
        
        # 返回最近的重要元素，优先返回前面的
        if prev_important and next_important:
            if editor_line - prev_important['line'] <= next_important['line'] - editor_line:
                return prev_important
            else:
                return next_important
        elif prev_important:
            return prev_important
        elif next_important:
            return next_important
        
        # 如果没有重要元素，就返回当前行
        return target_element 

    def sync_editor_to_preview(self, tab_index):
        """基本版同步方法，作为备用"""
        # 添加安全检查
        if tab_index not in self.tabs:
            return
            
        if self.is_syncing:
            return
            
        editor = self.tabs[tab_index]['editor']
        preview = self.tabs[tab_index]['preview']

        # 获取编辑器信息
        first_visible_line = editor.firstVisibleLine()
        total_lines = editor.lines()
        
        if total_lines <= 0:
            return
        
        # 计算当前编辑器的滚动比例 (0-1之间)
        scroll_ratio = first_visible_line / total_lines
        
        # 应用到预览区域
        scrollbar = preview.verticalScrollBar()
        total_scroll = scrollbar.maximum()
        
        # 设置预览区滚动位置 - 直接设置，不使用动画
        new_position = int(scroll_ratio * total_scroll)
        scrollbar.setValue(new_position)

    def start_smooth_scroll(self, tab_index, target_type, current_pos, target_pos):
        """简化版的滚动方法，直接设置到目标位置"""
        if target_type == 'editor':
            self.tabs[tab_index]['editor'].setFirstVisibleLine(target_pos)
        else:
            self.tabs[tab_index]['preview'].verticalScrollBar().setValue(target_pos) 