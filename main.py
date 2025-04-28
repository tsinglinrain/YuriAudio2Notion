from urllib.parse import urlparse, parse_qs
from datetime import datetime
import yaml
import os
import logging
import re
from notion_client_cus import NotionClient
from fanjiao_client import FanjiaoAPI, FanjiaoCVAPI
from descrip_process import DescriptionProcessor


from typing import List, Dict, Any

def acquire_data(
        fanjiao_api: FanjiaoAPI, 
        fanjiao_cv_api: FanjiaoCVAPI, 
        url: str) -> Dict[str, Any]:
    """acquire_data"""

    try:
        data_album_url: dict = {'album_url': url}
        data = fanjiao_api.fetch_album(url)
        data_relevant = fanjiao_api.extract_relevant_data(data)            
        
        print(f"测试:专辑名称: {data_relevant['name']}")
        
        data_cv = fanjiao_cv_api.fetch_album(url)
        data_cv = fanjiao_cv_api.extract_relevant_data(data_cv)
        
        print(f"测试:CV姓名: {data_cv['main_cv']}")
        print("-" * 20)
        data_ready = data_relevant | data_cv | data_album_url # Merge two dictionaries, Python 3.9+
        return data_ready
    
    except Exception as e:
        logging.error(f"处理 {url} 失败: {str(e)}")
        return None

def format_list_data(key, data: List[Dict]) -> List:
    """将cv和role分离
    
    map函数写法更简洁"""
    return list(map(lambda item: {"name": item.get(key, "")}, data))

def notion_para_get():
    with open("config_private.yaml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    notion_config = config.get("notion_config", {})
    database_id, token = (i for i in notion_config.values())
    return database_id, token

def upload_data(data_ready: Dict):
    """使用"""
    album_Link = data_ready.get("album_url", "")
    print(album_Link)
    name = data_ready.get("name", "")
    description = data_ready.get("description", "")
    
    property_cus = DescriptionProcessor()
    property_cus.description_get(description)
    property_cus.parse_property()

    description = property_cus.description
    description_sequel = property_cus.description_sequel
    print(description_sequel)
    up_name = property_cus.upname
    print(up_name)
    tags = property_cus.tag_list
    tags = property_cus.format_tag_list(tags)

    source = "改编" if "原著" in description_sequel else "原创" # 需要人工审阅

    publish_date: str = data_ready.get("publish_date", "")
    publish_date = publish_date.replace("+08:00", "Z") # publish_date = "2024-12-01T14:25:56+08:00" -> "2020-12-08T12:00:00Z”
    
    update_frequency = data_ready.get("update_frequency", "")
    ori_price = data_ready.get("ori_price", 0)
    author_name = data_ready.get("author_name", "")

    main_cv_ori: List = data_ready.get("main_cv", [])
    main_cv = format_list_data("name", main_cv_ori)
    print(main_cv)
    main_cv_role = format_list_data("role_name", main_cv_ori)
    print(main_cv_role)

    supporting_cv_ori: List = data_ready.get("supporting_cv", [])
    supporting_cv = format_list_data("name", supporting_cv_ori)
    supporting_cv_role = format_list_data("role_name", supporting_cv_ori)    
    
    commercial_drama = "商剧" if ori_price > 0 else "非商"
    
    episode_count = property_cus.episode_count

    database_id, token = notion_para_get()

    notion_client = NotionClient(database_id, token, "fanjiao")
    notion_client.cre_in_database_paper(
        name, 
        description,
        description_sequel, 
        publish_date, 
        update_frequency, 
        ori_price, 
        author_name,
        up_name,
        tags,
        source,
        main_cv,
        main_cv_role,
        supporting_cv,
        supporting_cv_role,
        commercial_drama,
        episode_count,
        album_Link
    )

def main():

    # 读取文件内容并生成URL列表
    url_list = []
    with open('waiting_up_private.txt', 'r', encoding="utf-8") as file:
        for line in file:
            # 去除首尾空白字符并添加到列表
            cleaned_url = line.strip()
            if cleaned_url:  # 确保非空行才添加到列表
                url_list.append(cleaned_url)

    # 验证结果（可选）
    print(f"共读取到 {len(url_list)} 个URL：")
    # for url in url_list:
    #     print(url)
    
    # try:
    fanjiao_api = FanjiaoAPI()
    fanjiao_cv_api = FanjiaoCVAPI()
    for url in url_list:
        data_ready = acquire_data(fanjiao_api, fanjiao_cv_api, url)
        if data_ready:
            upload_data(data_ready)
        else:
            print(f"处理 {url}后, 内容为空")
    # except Exception as e:
        # logging.error(f"处理 {url} 失败: {str(e)}")
if __name__ == "__main__":
    main()
