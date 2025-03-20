import json
import os
import requests
from urllib.parse import urlparse
import time
from pathlib import Path

def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    # 移除URL中的查询参数
    filename = filename.split('?')[0]
    # 获取文件扩展名
    ext = os.path.splitext(filename)[1]
    # 如果没有扩展名，添加.jpg
    if not ext:
        ext = '.jpg'
    # 移除非法字符
    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
    return filename

def download_image(url, save_path):
    """下载图片并保存到指定路径"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def main():
    # 创建images文件夹
    images_dir = Path('images')
    images_dir.mkdir(exist_ok=True)
    
    # 读取JSON文件
    try:
        with open('games_data.json', 'r', encoding='utf-8') as f:
            games_data = json.load(f)
    except Exception as e:
        print(f"Error reading games_data.json: {str(e)}")
        return
    
    # 下载图片
    total = len(games_data)
    success = 0
    failed = 0
    
    print(f"开始下载 {total} 个游戏的图片...")
    
    for i, game in enumerate(games_data, 1):
        if not game.get('image_url'):
            print(f"[{i}/{total}] 跳过 {game['title']}: 没有图片URL")
            failed += 1
            continue
            
        # 生成文件名
        filename = sanitize_filename(f"{game['title']}{os.path.splitext(game['image_url'])[1]}")
        save_path = images_dir / filename
        
        # 如果文件已存在，跳过
        if save_path.exists():
            print(f"[{i}/{total}] 跳过 {game['title']}: 文件已存在")
            success += 1
            continue
        
        print(f"[{i}/{total}] 下载 {game['title']} 的图片...")
        
        if download_image(game['image_url'], save_path):
            success += 1
            print(f"成功下载: {filename}")
        else:
            failed += 1
            print(f"下载失败: {filename}")
        
        # 添加短暂延迟，避免请求过快
        time.sleep(0.5)
    
    print(f"\n下载完成!")
    print(f"总数: {total}")
    print(f"成功: {success}")
    print(f"失败: {failed}")

if __name__ == '__main__':
    main()