import PyInstaller.__main__
import os
from PIL import Image

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定义图标路径
icon_png = os.path.join(current_dir, 'resources', 'icon.png')
icon_ico = os.path.join(current_dir, 'resources', 'icon.ico')

# 转换图标格式
if os.path.exists(icon_png):
    img = Image.open(icon_png)
    img.save(icon_ico, format='ICO')
    icon_path = icon_ico
else:
    icon_path = None

# 定义打包参数
params = [
    'src/main.py',  # 主程序文件
    '--name=MarkGT',  # 生成的exe名称
    '--windowed',  # 使用GUI模式
    '--noconfirm',  # 不询问确认
    '--clean',  # 清理临时文件
    '--add-data=resources;resources',  # 添加资源文件夹
    '--hidden-import=PyQt6.Qsci',  # 添加隐藏导入
    '--hidden-import=mistune',
    '--collect-all=PyQt6',  # 收集所有PyQt6相关文件
    '--collect-all=PyQt6.Qsci',  # 收集所有Qsci相关文件
    '--collect-all=PyQt6.Qt6',  # 收集所有Qt6相关文件
    '--collect-all=PyQt6.Qt6.plugins',  # 收集所有Qt6插件
    '--collect-all=PyQt6.Qt6.plugins.platforms',  # 收集平台插件
    '--collect-all=PyQt6.Qt6.plugins.styles',  # 收集样式插件
    '--collect-all=PyQt6.Qt6.plugins.imageformats',  # 收集图片格式插件
]

# 如果图标存在，添加到参数中
if icon_path:
    params.append(f'--icon={icon_path}')

# 执行打包
PyInstaller.__main__.run(params) 