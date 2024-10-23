# -*- coding: utf-8 -*-
"""
Created on Sun Oct 20 22:57:53 2024

@description: 提取包含“三月七”关键词的页面的编辑源文本内容，并存储到Pandas DataFrame中。
             将数据保存到指定路径，并在文件名中包含页面标题。加入延迟功能，确保请求发送不频繁。

@author: Administrator
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import urllib.parse  # 用于URL编码
import time  # 用于添加延迟

def write_dataframe_to_path(df: pd.DataFrame, title: str):
    """
    将传入的 DataFrame 写入指定路径，文件名包含页面标题。

    参数:
    df (pd.DataFrame): 要写入的 DataFrame。
    title (str): 页面标题，用于生成文件名。
    """
    # 定义目标路径
    path = r'C:\ruoyi\March7th'

    # 检查路径是否存在，如果不存在则创建
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            print(f"已创建路径: {path}")
        except Exception as e:
            print(f"创建路径时出错: {e}")
            return

    # 生成文件名，确保合法文件名（去除可能的非法字符）
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
    filename = f"{safe_title}_edit_page_content.csv"

    # 组合完整的文件路径
    full_path = os.path.join(path, filename)

    try:
        # 将 DataFrame 写入 CSV 文件
        df.to_csv(full_path, index=False, encoding='utf-8-sig')
        print(f"DataFrame 已成功写入 {full_path}")
    except Exception as e:
        print(f"写入文件时出错: {e}")
def fetch_edit_page_content(api_url, title):
    """
    获取指定页面的编辑源文本内容。

    参数:
        api_url (str): MediaWiki 的基础 URL。
        title (str): 需要获取的页面标题。

    返回:
        str: 页面编辑源文本内容。如果请求失败，返回空字符串。
    """
    import urllib.parse  # 确保引入了 urllib.parse
    import time  # 引入 time 模块用于延迟

    max_retries = 5
    retry_delay = 1  # 每次重试之间的等待时间（秒）
    attempts = 0

    while attempts < max_retries:
        try:
            # 对页面标题进行URL编码
            encoded_title = urllib.parse.quote(title)
            # 构造编辑页面的 URL
            edit_url = f"{api_url}/index.php?title={encoded_title}&action=edit"

            # 发送请求获取页面
            response = requests.get(edit_url)
            if response.status_code == 200:
                # 解析HTML页面
                soup = BeautifulSoup(response.text, 'html.parser')
                # 查找页面中的文本编辑区域
                textarea = soup.find('textarea')
                if textarea:
                    return textarea.get_text()  # 返回页面源文本内容
                else:
                    print("未找到编辑页面的文本区域。")
                    return ""
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except Exception as e:
            print(f"获取页面内容时出错: {e}")

        attempts += 1
        if attempts < max_retries:
            print(f"请求失败，等待 {retry_delay} 秒后重试... (第 {attempts} 次重试)")
            time.sleep(retry_delay)
        else:
            print(f"请求失败，已重试 {attempts} 次，跳过页面：{title}")
            return ""
    return ""

def extract_text_from_edit_page(content):
    """
    从编辑页面的源文本内容中提取所有文本，并根据规则分类。
    当一行包含“：”或“剧情”时，提取“：”之前的文本，从“：”向前提取到出现第一个符号，将这段无符号的文本填入character。

    参数:
        content (str): 编辑页面的源文本内容。

    返回:
        list of dict: 包含提取的文本数据的字典列表。
    """
    extracted_data = []
    import re  # 确保引入了正则表达式模块

    # 按行分割内容，逐行处理
    lines = content.splitlines()
    for line_num, line in enumerate(lines, 1):
        # 初始化 category 和 character
        category = 'default'
        character = ''

        # 去除每行的首尾空格
        stripped_line = line.strip()

        # 首先检查是否包含 '剧情选项' 或 '剧情内容'
        if '剧情选项' in line or '剧情内容' in line:
            category = 'default'
        else:
            # 根据规则确定 category，优先级："剧情" > "选项" > "："
            if '剧情' in line:
                category = 'branch_content'
            elif '选项' in line:
                category = 'option'
                character = '开拓者'  # 直接将 character 设置为 '开拓者'
            elif '：' in line:
                category = 'content'

            # 当行包含 '：' 时，提取 character
            if '：' in line:
                # 提取“：”之前的文本
                before_colon = line.split('：')[0]

                # 使用正则表达式，反向查找最后一个连续的汉字序列
                matches = re.findall(r'[\u4e00-\u9fa5]+', before_colon)
                if matches:
                    character = matches[-1]  # 取最后一个匹配的汉字序列
                else:
                    character = ''
            # 保持 character 为 '开拓者' 如果 category 为 'option'
            elif category == 'option':
                character = '开拓者'

        extracted_data.append({
            'line_number': line_num,
            'content': stripped_line,
            'category': category,
            'character': character  # 更新的列
        })

    return extracted_data





def get_all_page_titles(api_url):
    """
    获取 wiki 站点上所有页面的标题列表。

    参数:
        api_url (str): MediaWiki 的基础 URL。

    返回:
        list of str: 页面标题列表。
    """
    titles = []
    aplimit = 500  # 每次请求的最大页面数
    apcontinue = ''
    while True:
        params = {
            'action': 'query',
            'list': 'allpages',
            'format': 'json',
            'aplimit': aplimit,
        }
        if apcontinue:
            params['apcontinue'] = apcontinue
        response = requests.get(api_url + '/api.php', params=params)
        data = response.json()
        pages = data['query']['allpages']
        for page in pages:
            titles.append(page['title'])
        if 'continue' in data:
            apcontinue = data['continue']['apcontinue']
        else:
            break
    return titles

def main():
    # 基础 MediaWiki API URL
    api_url = "https://wiki.biligame.com/sr"

    # 获取所有页面的标题
    page_titles = get_all_page_titles(api_url)
    print(f"共获取到 {len(page_titles)} 个页面标题。")
    # page_titles = [
    #     "初花剑客行•剑斗",
    #     "初花剑客行•祓除",
    #     "初花剑客行•辩辞",
    #     "初花剑客行•泄火",
    #     "初花剑客行•夺主"
    # ]

    for page_title in page_titles:
        print(f"正在处理页面：{page_title}")

        # 获取页面的编辑源文本内容
        content = fetch_edit_page_content(api_url, page_title)
        if not content:
            print(f"未能获取页面 {page_title} 的内容。")
        else:
            # 判断页面内容中是否包含 "三月七"
            if "三月七" in content:
                print(f"页面 {page_title} 包含 '三月七'，开始提取。")
                # 提取文本内容
                extracted_data = extract_text_from_edit_page(content)

                if not extracted_data:
                    print(f"未找到页面 {page_title} 的文本内容。")
                else:
                    # 将提取的数据转换为Pandas DataFrame
                    df = pd.DataFrame(extracted_data)

                    # 将DataFrame保存到指定路径，传入页面标题
                    write_dataframe_to_path(df, page_title)
            else:
                print(f"页面 {page_title} 不包含 '三月七'，跳过。")

        # 加入延迟，确保请求不频繁
        time.sleep(1)  # 延迟1秒

if __name__ == "__main__":
    main()
