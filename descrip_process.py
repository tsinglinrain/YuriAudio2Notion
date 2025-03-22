import requests
from notion_client import Client
import yaml
import re

from typing import Dict, List, Tuple, Any

class DescriptionProcessor():
    def __init__(self):
        self.description_ori: str = None
        self.description: str = None
        self.description_sequel: str = None
        self.upname: str = None
        self.tag_list: List = None

    def description_get(self, description_ori: str):
        '''更改或获取description_ori'''
        self.description_ori: str = description_ori
        # print(self.description_ori)

    def parse_property(self):
        self.description, self.description_sequel = self.description_split()
        self.upname: str = self.description_upname()
        self.tag_list: List = self.description_tag()

    def description_split(self) -> Tuple[str, str]:
        """将描述分割成段落"""
        # 找到"出品"的位置
        start = self.description_ori.find("出品")
        if start == -1:
            return [self.description_ori, ""]
        
        # 向前查找最近的换行符
        split_index = self.description_ori.rfind('\n', 0, start)
        if split_index == -1:
            return [self.description_ori, ""]
        

        # 分割字符串，并移除换行符
        part1 = self.description_ori[ :split_index-1]
        part2 = self.description_ori[split_index+1: ]
        return [part1, part2]
        
    def description_upname(self) -> str:
        """up_name提取, 不准确, 需要人工审核"""
        # 优先匹配"制作出品"或"出品制作"前的最后一个逗号分割的内容
        combined_match = re.search(r'，([^，]+?)(?=制作出品|出品制作)', self.description_sequel)
        if combined_match:
            return combined_match.group(1).strip()
        
        # 检查是否存在"制作"
        produce_match = re.search(r'，([^，]+?)(?=制作)', self.description_sequel)
        if produce_match:
            up_name_temp = produce_match.group(1).strip()
            # 如果存在多个名称，以逗号或顿号分隔，取第一个
            if '、' in up_name_temp:
                return up_name_temp.split('、')[0].strip()
            return up_name_temp
    
        # 检查是否存在"出品"
        publish_match = re.search(r'，([^，]+?)(?=出品)', self.description_sequel)
        if publish_match:
            up_name_temp = publish_match.group(1).strip()
            if '、' in up_name_temp:
                return up_name_temp.split('、')[0].strip()
            return up_name_temp
        
        # 无匹配情况
        return ""

    def description_tag(self) -> list:
        '''广播剧'''
        match = re.search(r'，([^，]+?)广播剧《', self.description_sequel)
        if not match:
            return []
        
        tags_str = match.group(1).strip()
        tags_str = tags_str.replace('百合', '')   # 只爱百广, 剔除固有标签
        tag_list = []
        
        # 处理“全一季”标签
        if '全一季' in tags_str:
            # tag_list.append('全一季')   # 纠结了一下, 还是给注释掉了, 更像强调题材风格
            tags_str = tags_str.replace('全一季', '')
        
        # 分割剩余内容为标签
        if tags_str:
            chunk_size = 2
            # 根据长度决定是否分割为两字标签
            if len(tags_str) % chunk_size == 0:
                remaining_tags = [tags_str[i:i+chunk_size] for i in range(0, len(tags_str), chunk_size)]
            else:
                remaining_tags = [tags_str]
            tag_list.extend(remaining_tags)
        
        return tag_list
    

    def desc_ep_count(self) -> int:
        '''description_episode_count'''
        
        
        # 正则表达式匹配正剧后的集数信息
        pattern = r'正剧.*?(?:共\D*?)?(\d+|[一二两三四五六七八九十]+)[集期，]'
        match = re.search(pattern, self.description_sequel)
        if not match:
            return 0
        
        num_str = match.group(1)
        
        # 中文数字到阿拉伯数字的映射
        chinese_num = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
            '七': 7, '八': 8, '九': 9, '十': 10, '两': 2, '0': 0,
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
            '7': 7, '8': 8, '9': 9
        }
        
        # 处理阿拉伯数字
        if num_str.isdigit():
            return int(num_str)
        
        # 处理中文数字
        total = 0
        for char in num_str:
            if char in chinese_num:
                total += chinese_num[char]
            else:
                return 0  # 遇到无法识别的字符返回0
        return total if total != 0 else 0

    @staticmethod
    def format_tag_list(data: List) -> List:
        """将tags list formated"""
        formatted_data = []
        for item in data:
            formatted_data.append(
                {
                    "name": item,
                }
            )
        return formatted_data   


def main():
    description = "琴声起，不知情始。\n弦音落，难解情痴。\n\n中州皇族势微，天下被五大藩王割据，混战间风雨飘摇。而五藩之中，属崟王势力最盛。\n\n女伶曲红绡初入崟王府，眼看着就要摇身变为世子侍妾，却被冠以狐媚惑主之名，险些被逐出王府。幸好得郡主卫璃攸收留，才勉强有了容身之所，殊不知看似病弱无害的郡主，才是真正的狐狸。\n\n[奴婢可有选择的余地？]\n[你自然是——没得选。]\n\n利用，权衡，挣扎，沉沦......血雨腥风，暗流涌动；身世浮沉，命难由己。\n\n长佩文学，闻人碎语原著，仟金不换工作室出品，古风百合广播剧《落音记》第一季。本剧共两季，第一季正剧共更广告，每期时长均在30分钟以上，定期掉落花絮，不定期掉落小剧场、福利，12月16日起每周一中午十二点更新，欢迎收听。\n\n追剧日历：\n12月6日：主题曲\n12月9日：预告\n12月12日：主役前采\n12月14日：楔子 曲红绡篇\n12月15日：楔子 卫璃攸篇\n12月16日：第一期\n\n禁止盗版、篡改、用于其他商业用途等行为，违者必追究法律责任。"
    property_cus = DescriptionProcessor()
    property_cus.description_get(description)
    
    
    property_cus.parse_property()
    # print(property_cus.description)
    description = property_cus.description
    description_sequel = property_cus.description_sequel
    up_name = property_cus.upname
    tags = property_cus.tag_list
    tags = property_cus.format_tag_list(tags)

    episode_count = property_cus.desc_ep_count()
    print(episode_count)
    # for i in [description, description_sequel, up_name, tags]:
    #     print(i)
    #     print("*"*20)
    #     print("\n")

if __name__ == "__main__":
    main()
