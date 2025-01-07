import os
import shutil
import re
from loguru import logger
from pylatexenc.latex2text import LatexNodes2Text

def remove_images_and_references(md_content):
    md_content = LatexNodes2Text().latex_to_text(md_content)
    # 移除图片引用
    md_content = re.sub(r'!\[.*?\]\(.*?\)', '', md_content, flags=re.DOTALL)
    # 移除末尾的 references 部分

    lines = md_content.split('\n')
    final = []
    for line in lines:
        if '# LITERATURE CITED' in line:
            break
        if '参考文献:' in line:
            break
        if '# REFERENCES' in line:
            break
        if '# 参考文献' in line:
            break
        if '# References' in line:
            break
        final.append(line.strip())
    
    md_content_remove_ref = '\n'.join(final)
    md_content_remove_ref = md_content_remove_ref.replace('','')
    md_content_remove_ref = md_content_remove_ref.replace('','')
    return md_content_remove_ref

def process_md_files(source_dir, output_dir):
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 遍历目录
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as md_file:
                    md_content = md_file.read()
                
                # 处理md文件内容
                processed_content = remove_images_and_references(md_content)
                
                # 构建输出文件路径
                # relative_path = os.path.relpath(file_path, source_dir)
                basename = os.path.basename(file_path)
                output_file_path = os.path.join(output_dir, basename)
                
                # 确保输出文件的目录存在
                output_file_dir = os.path.dirname(output_file_path)
                if not os.path.exists(output_file_dir):
                    os.makedirs(output_file_dir)
                
                # 写入处理后的内容到输出文件
                with open(output_file_path, 'w', encoding='utf-8') as output_md_file:
                    output_md_file.write(processed_content)
                print(f'Processed and copied {file} to {output_file_path}')

# 设置源目录和输出目录
source_dir = '/home/wangzhefan/pdfs-text'
output_dir = '/home/khj/workspace/HuixiangDou/repodir'

# 处理md文件
process_md_files(source_dir, output_dir)
