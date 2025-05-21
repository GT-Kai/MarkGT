# MarkGT

A sleek and elegant Markdown editor that provides real-time preview and a comfortable writing experience.

<div align="center">
  <!-- Project logo or screenshot can be added here -->
</div>

## Features

- **Real-time Preview**: Edit Markdown text on the left, see the rendered result instantly on the right
- **Syntax Highlighting**: Support for Markdown syntax coloring to enhance editing experience
- **Multiple Tabs**: Edit multiple documents simultaneously to improve productivity
- **Custom Toolbar**: Quick insertion of common Markdown syntax
- **Split View**: Adjustable ratio between editor and preview areas
- **Word Wrap**: Intelligent line wrapping based on window size for comfortable reading
- **File Management**: Support for basic operations like creating, opening, and saving files

## Requirements

- Python 3.8+
- Dependencies:
  - PyQt6 6.6.1+
  - PyQt6-QScintilla 2.14.1+
  - mistune 3.0.2+
  - markdown 3.5.2+
  - pygments 2.17.2+
  - watchdog 3.0.0+
  - pillow

## Installation

### Install Executable

1. Download the latest version from [Releases](https://github.com/GT—Kai/MarkGT/releases)
2. Extract and run `MarkGT.exe`

### Install from Source

1. Clone the repository
   ```bash
   git clone https://github.com/GT—Kai/MarkGT.git
   cd MarkGT
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Run the program
   ```bash
   python src/main.py
   ```

4. (Optional) Build executable
   ```bash
   python build.py
   ```
   The generated executable will be in the `dist` directory.

## User Guide

### Basic Operations

- **New File**: Ctrl+N or click "New" in the "File" menu
- **Open File**: Ctrl+O or click "Open" in the "File" menu
- **Save File**: Ctrl+S or click "Save" in the "File" menu
- **Save As**: Ctrl+Shift+S or click "Save As" in the "File" menu

### Markdown Toolbar

The toolbar provides quick insertion buttons for common Markdown syntax:

- **Headers**: H1, H2, H3
- **Lists**: Unordered list, Ordered list
- **Code**: Code block, Inline code
- **Table**: Insert table template
- **Links and Images**: Quick insertion of link and image markers

### View Adjustments

- **Word Wrap**: Toggle editor word wrap through the "View" menu
- **Split View**: Adjust the ratio between editor and preview areas

## Contributing

Contributions to the MarkGT project are welcome! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development Plan

- [ ] More theme support
- [ ] Export to PDF, HTML functionality
- [ ] Spell checking
- [ ] Cloud sync functionality
- [ ] Plugin system

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Contact

Author Email： 2975177159@qq.com

Project Author - [@yourusername](https://github.com/GT—Kai)

Project Link: [https://github.com/yourusername/MarkGT](https://github.com/GT—Kai/MarkGT) 