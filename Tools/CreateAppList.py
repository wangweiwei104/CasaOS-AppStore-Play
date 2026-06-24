import glob
import os
import yaml
import re
import urllib.request
import ssl

def convert_icon_url(icon_url):
    """将CDN URL转换为相对路径，支持任意目录名"""
    if not icon_url:
        return icon_url
    
    # 匹配 jsdelivr CDN 模式，支持任意目录名
    patterns = [
        r'https://cdn\.jsdelivr\.net/gh/[^/]+/[^/@]+@[^/]+/([^/]+)/(.+)$',  # 带 @branch 的
        r'https://cdn\.jsdelivr\.net/gh/[^/]+/[^/]+/([^/]+)/(.+)$',         # 不带 @branch 的
    ]
    
    for pattern in patterns:
        match = re.match(pattern, icon_url)
        if match:
            folder_type = match.group(1)  # 任意目录名
            relative_path = match.group(2)  # 剩余路径
            return f"{folder_type}/{relative_path}"
    
    # 如果不是CDN链接，保持原样
    return icon_url

def download_icon(icon_url, local_path):
    """下载图标文件到本地"""
    if not icon_url or icon_url.startswith(('Apps/', 'Apps_arm/', './')):
        return False
    
    try:
        # 创建目录（如果不存在）
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # 设置SSL上下文，避免证书验证问题
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # 下载文件
        with urllib.request.urlopen(icon_url, context=ssl_context, timeout=10) as response:
            with open(local_path, 'wb') as f:
                f.write(response.read())
        print(f"✓ 已下载: {local_path}")
        return True
    except Exception as e:
        print(f"✗ 下载失败 {icon_url}: {e}")
        return False

# 获取两个路径下的文件列表
apps_files = glob.glob('./Apps/*/docker-compose.yml')
apps_arm_files = glob.glob('./Apps_arm/*/docker-compose.yml')

# 初始化Markdown表格
markdown_table = "| Icon | AppName | Description |\n"
markdown_table += "|:----:|---------|-------------|\n"

# 记录已处理的app名称
processed_apps = set()

# 处理 ./Apps/*/docker-compose.yml
for compose_file in apps_files:
    with open(compose_file, 'r', encoding='utf-8') as f:
        try:
            data = yaml.safe_load(f)
            app_name = os.path.basename(os.path.dirname(compose_file))
            
            # 记录已处理的app
            processed_apps.add(app_name)
            
            original_icon = data.get('x-casaos', {}).get('icon', '')
            # 转换图标URL为相对路径
            icon = convert_icon_url(original_icon)
            
            # 检查本地文件是否存在，如果不存在则下载
            if original_icon and original_icon.startswith('http'):
                local_icon_path = icon
                if not os.path.exists(local_icon_path):
                    print(f"正在下载 {app_name} 的图标...")
                    download_icon(original_icon, local_icon_path)
            
            title = data.get('x-casaos', {}).get('title', {}).get('en_us', '')
            description1 = data.get('x-casaos', {}).get('description', {}).get('en_us', '').replace("\n", "")
            description2 = data.get('x-casaos', {}).get('description', {}).get('zh_cn', '').replace("\n", "")
            
            if description1 == description2:
                description = description1
            elif description1 == "":
                description = description2
            else:
                description = f"{description1}<br>{description2}"

            markdown_table += f"| ![{title}]({icon}) | [{title}](./Apps/{app_name}) | {description} |\n"
        except Exception as e:
            print(f"Error parsing {compose_file}: {e}")

# 处理 ./Apps_arm/*/docker-compose.yml（跳过已处理的app）
for compose_file in apps_arm_files:
    with open(compose_file, 'r', encoding='utf-8') as f:
        try:
            data = yaml.safe_load(f)
            app_name = os.path.basename(os.path.dirname(compose_file))
            
            # 跳过已处理的app
            if app_name in processed_apps:
                continue
                
            original_icon = data.get('x-casaos', {}).get('icon', '')
            # 转换图标URL为相对路径
            icon = convert_icon_url(original_icon)
            
            # 检查本地文件是否存在，如果不存在则下载
            if original_icon and original_icon.startswith('http'):
                local_icon_path = icon
                if not os.path.exists(local_icon_path):
                    print(f"正在下载 {app_name} 的图标...")
                    download_icon(original_icon, local_icon_path)
            
            title = data.get('x-casaos', {}).get('title', {}).get('en_us', '')
            description1 = data.get('x-casaos', {}).get('description', {}).get('en_us', '').replace("\n", "")
            description2 = data.get('x-casaos', {}).get('description', {}).get('zh_cn', '').replace("\n", "")
            
            if description1 == description2:
                description = description1
            elif description1 == "":
                description = description2
            else:
                description = f"{description1}<br>{description2}"

            markdown_table += f"| ![{title}]({icon}) | [{title}](./Apps_arm/{app_name}) | {description} |\n"
        except Exception as e:
            print(f"Error parsing {compose_file}: {e}")

# 将Markdown表格写入README.md文件
file_path = 'README.md'
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

new_content = re.sub(
    r'(## App List / 应用列表)([\w\W]*)',
    '## App List / 应用列表\n\n' + markdown_table,
    content
)

with open(file_path, 'w', encoding='utf-8') as file:
    file.write(new_content)

print("已生成")