import sys
from cx_Freeze import setup, Executable

# 依赖项
build_exe_options = {
    "packages": ["os", "sys", "PyQt6", "PyQt6.Qsci", "mistune"],
    "excludes": [],
    "include_files": [
        ("resources", "resources"),
    ]
}

# 文件关联配置
file_associations = [
    ("Markdown Files", "*.md", "MarkGT", "MarkGT", "MarkGT Markdown Editor")
]

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="MarkGT",
    version="1.0",
    description="Markdown Editor",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "src/main.py",
            base=base,
            target_name="MarkGT.exe",
            icon="resources/icon.ico",
            shortcut_name="MarkGT",
            shortcut_dir="DesktopFolder",
            file_associations=file_associations
        )
    ]
) 