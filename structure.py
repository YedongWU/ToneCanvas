import os

# 手动定义要忽略的文件和目录
IGNORED_PATHS = [
    'backend/.env',
    'frontend/node_modules',
]

def should_ignore(path, ignored_paths):
    # 转换路径为相对路径
    relative_path = os.path.relpath(path, start=os.getcwd())
    
    # 检查是否在忽略的路径列表中
    for ignore in ignored_paths:
        # 如果路径是目录，检查是否以此目录开头
        if os.path.isdir(ignore) and relative_path.startswith(ignore):
            return True
        # 如果路径是文件，直接匹配
        elif os.path.isfile(ignore) and relative_path == ignore:
            return True
    return False

def print_directory_structure(root_dir, ignored_paths, indent=''):
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        
        # 跳过忽略的文件和目录
        if should_ignore(item_path, ignored_paths):
            continue
        
        if os.path.isdir(item_path):
            print(f"{indent}📁 {item}/")
            print_directory_structure(item_path, ignored_paths, indent + '    ')
        else:
            print(f"{indent}📄 {item}")

if __name__ == "__main__":
    current_dir = os.getcwd()
    
    print(f"Directory structure for: {current_dir}\n")
    print_directory_structure(current_dir, IGNORED_PATHS)
