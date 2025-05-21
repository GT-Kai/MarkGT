#### 不足7所引发的问题
6. DLL 添加脚本自动化
```
# === 自动添加所需DLL ===
NEEDED_DLLS = [
    'Qt6Network.dll',
    'Qt6WebSockets.dll',
    # 你还可以继续加其它需要的 DLL
]
qt_bin_dir = os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6', 'bin')
for dll in NEEDED_DLLS:
    dll_path = os.path.join(qt_bin_dir, dll)
    if os.path.exists(dll_path):
        params.append(f'--add-binary={dll_path};.')
    else:
        print(f'警告: 未找到 {dll_path}')
```