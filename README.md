# MarkGT

一款简洁优雅的Markdown编辑器，提供实时预览与舒适的写作体验。

<div align="center">
  <!-- 这里可以添加项目logo或截图 -->
</div>

## 功能特点

- **实时预览**: 左侧编辑Markdown文本，右侧即时展示渲染效果
- **语法高亮**: 支持Markdown语法着色，提升编辑体验
- **多标签页**: 同时编辑多个文档，提高工作效率
- **自定义工具栏**: 便捷插入常用Markdown语法
- **分割视图**: 可调整编辑区与预览区的比例
- **自动换行**: 根据窗口大小智能换行，提供舒适阅读体验
- **文件管理**: 支持创建、打开、保存文件等基本操作

## 安装要求

- Python 3.8+
- 依赖包：
  - PyQt6 6.6.1+
  - PyQt6-QScintilla 2.14.1+
  - mistune 3.0.2+
  - markdown 3.5.2+
  - pygments 2.17.2+
  - watchdog 3.0.0+
  - pillow

## 安装步骤

### 安装可执行程序

1. 从[Releases](https://github.com/GT-Kai/MarkGT/releases)下载最新版本
2. 解压后双击运行`MarkGT.exe`

### 从源码安装

1. 克隆仓库
   ```bash
   git clone https://github.com/GT-Kai/MarkGT.git
   cd MarkGT
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 运行程序
   ```bash
   python src/main.py
   ```

4. （可选）构建可执行文件
   ```bash
   python build.py
   ```
   生成的可执行文件将位于`dist`目录下。

## 使用指南

### 基本操作

- **新建文件**: Ctrl+N 或点击"文件"菜单中的"新建"
- **打开文件**: Ctrl+O 或点击"文件"菜单中的"打开"
- **保存文件**: Ctrl+S 或点击"文件"菜单中的"保存"
- **另存为**: Ctrl+Shift+S 或点击"文件"菜单中的"另存为"

### Markdown工具栏

工具栏提供了常用Markdown语法的快捷插入按钮：

- **标题**: H1、H2、H3
- **列表**: 无序列表、有序列表
- **代码**: 代码块、行内代码
- **表格**: 插入表格模板
- **链接和图片**: 快速插入链接和图片标记

### 视图调整

- **自动换行**: 通过"视图"菜单可切换编辑器的自动换行功能
- **分割视图**: 可以调整编辑区和预览区的比例

## 贡献指南

欢迎对MarkGT项目做出贡献！请遵循以下步骤：

1. Fork本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个Pull Request

## 开发计划

- [ ] 更多主题支持
- [ ] 导出PDF、HTML功能
- [ ] 拼写检查
- [ ] 云同步功能
- [ ] 插件系统

## 许可证

该项目采用 MIT 许可证 - 详情请参见 [LICENSE](LICENSE) 文件

## 联系方式

项目作者 - [@yourusername](https://github.com/GT—Kai)

项目链接: [https://github.com/yourusername/MarkGT](https://github.com/yourusername/MarkGT) 