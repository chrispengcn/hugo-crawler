import os
import argparse

def replace_in_file(file_path, source_str, target_str):
    """替换单个文件中的字符串"""
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 检查是否需要替换
        if source_str not in content:
            return False
        
        # 执行替换
        new_content = content.replace(source_str, target_str)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        return True
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
        return False

def find_and_replace(root_dir, source_str, target_str, dry_run=False):
    """递归查找并替换所有.md文件中的字符串"""
    count = 0
    modified_files = []
    
    # 遍历目录
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            # 只处理.md文件
            if filename.lower().endswith('.md'):
                file_path = os.path.join(dirpath, filename)
                
                # 检查文件中是否包含源字符串
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    if source_str in content:
                        modified_files.append(file_path)
                        if not dry_run:
                            if replace_in_file(file_path, source_str, target_str):
                                count += 1
                except Exception as e:
                    print(f"检查文件 {file_path} 时出错: {str(e)}")
    
    if dry_run:
        return modified_files, 0
    return modified_files, count

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='替换Markdown文件中的字符串')
    parser.add_argument('--root', default='.', help='文档根目录，默认为当前目录')
    parser.add_argument('--source', required=True, help='要被替换的源字符串')
    parser.add_argument('--target', required=True, help='替换后的目标字符串')
    parser.add_argument('--force', action='store_true', help='强制替换，不进行确认')
    
    args = parser.parse_args()
    
    # 验证根目录是否存在
    if not os.path.isdir(args.root):
        print(f"错误: 目录 '{args.root}' 不存在")
        return
    
    # 先执行一次干运行，查看哪些文件会被修改
    print(f"正在搜索目录 '{args.root}' 下所有包含 '{args.source}' 的.md文件...")
    modified_files, _ = find_and_replace(args.root, args.source, args.target, dry_run=True)
    
    if not modified_files:
        print("没有找到需要修改的文件")
        return
    
    # 显示将要修改的文件
    print(f"\n找到 {len(modified_files)} 个包含 '{args.source}' 的文件:")
    for file_path in modified_files:
        print(f"  - {file_path}")
    
    # 确认是否执行替换
    if not args.force:
        confirm = input(f"\n确定要将所有文件中的 '{args.source}' 替换为 '{args.target}' 吗? (y/n) ")
        if confirm.lower() not in ['y', 'yes']:
            print("操作已取消")
            return
    
    # 执行替换
    print("\n正在执行替换...")
    _, count = find_and_replace(args.root, args.source, args.target)
    
    print(f"\n替换完成，共修改了 {count} 个文件")

if __name__ == "__main__":
    main()
    