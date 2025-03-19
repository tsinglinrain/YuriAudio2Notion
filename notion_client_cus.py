import requests
from notion_client import Client
import yaml

class NotionClient:
    def __init__(self, database_id, token, payment_platform):
        self.database_id = database_id
        self.token = token
        self.client: Client = Client(auth=token)
        self.payment_platform = payment_platform

    def create_page(self, properties):
        """Create a new page in the database"""

        try:
            self.client.pages.create(
                icon = {
                    "type": "emoji",
                    "emoji": "🎧"   # 非常贴合,堪称完美图标
                },
                # cover # 也没有需求
                parent={"database_id": self.database_id},
                properties=properties,
                # children=blocks,  # 不要children
            )
            print("Page created successfully\n上传成功")
        except Exception as e:
            print(f"Failed to create page: {e}")
            print("-" * 20)
            print("上传失败,自动跳过,请自行检查")

    def cre_in_database_paper(
            self, 
            name, 
            description, 
            description_sequel,
            publish_date, 
            update_frequency, 
            ori_price, 
            author_name,
            main_cv,
            main_cv_role,
            supporting_cv,
            supporting_cv_role,
            commercial_drama,
            platform="饭角",
            time_zone="Asia/Shanghai"
        ):
        """Create a new page in the database"""
        properties = {
            "Name": {"title": [{"text": {"content": name}}]},
            "简介": {"rich_text": [{"text": {"content": description}}]},
            "简介续": {"rich_text": [{"text": {"content": description_sequel}}]},
            "Publish Date": {
                "date": {
                    "start": publish_date,
                    "time_zone": time_zone,  # 时区, 参见官方文档
                }
            },
            "更新": {"select": {"name": update_frequency}},
            "Price": {"number": ori_price},
            "原著": {"select": {"name": author_name}},
            "cv主役":{"multi_select": main_cv},
            "饰演角色": {"multi_select": main_cv_role},
            "cv协役": {"multi_select": supporting_cv},
            "协役饰演角色": {"multi_select": supporting_cv_role},
            "商剧": {"select": {"name": commercial_drama}},
            "Platform": {"multi_select": [{"name": platform}]},
        }
        self.create_page(properties)

def description_split(description: str) -> list[str, str]:
    """将描述分割成段落"""
    # 找到“出品”的位置
    start = description.find("出品")
    if start == -1:
        return [description, ""]
    
    # 向前查找最近的换行符
    split_index = description.rfind('\n', 0, start)
    if split_index == -1:
        return [description, ""]
    
    # 分割字符串，并移除换行符
    part1 = description[ :split_index-1]
    part2 = description[split_index+1: ]
    return [part1, part2]
    

def main():
    """示例使用"""
    name = "落音记 第一季"
    description = "琴声起，不知情始。\n弦音落，难解情痴。\n\n中州皇族势微，天下被五大藩王割据，混战间风雨飘摇。而五藩之中，属崟王势力最盛。\n\n女伶曲红绡初入崟王府，眼看着就要摇身变为世子侍妾，却被冠以狐媚惑主之名，险些被逐出王府。幸好得郡主卫璃攸收留，才勉强有了容身之所，殊不知看似病弱无害的郡主，才是真正的狐狸。\n\n[奴婢可有选择的余地？]\n[你自然是——没得选。]\n\n利用，权衡，挣扎，沉沦......血雨腥风，暗流涌动；身世浮沉，命难由己。\n\n长佩文学，闻人碎语原著，仟金不换工作室出品，古风百合广播剧《落音记》第一季。本剧共两季，第一季正剧共十期，每期时长均在30分钟以上，定期掉落花絮，不定期掉落小剧场、福利，12月16日起每周一中午十二点更新，欢迎收听。\n\n追剧日历：\n12月6日：主题曲\n12月9日：预告\n12月12日：主役前采\n12月14日：楔子 曲红绡篇\n12月15日：楔子 卫璃攸篇\n12月16日：第一期\n\n禁止盗版、篡改、用于其他商业用途等行为，违者必追究法律责任。"
    description, description_sequel = description_split(description)
    # horizontal = "https://fanjiao-media.fanjiao.co/Fgzc5o5EKjfMEvl-pIoRtialfCJ2?imageMogr2/crop/!850x519.4444444444445a0a0/format/png/thumbnail/400x"
    # publish_date = "2024-12-01T14:25:56+08:00"
    publish_date = "2024-12-01T14:25:56Z"
    # "2020-12-08T12:00:00Z”
    update_frequency = "已完结"
    ori_price = 218
    author_name = "闻人碎语"
    main_cv = [{'name': '纸巾'}, {'name': '清鸢'}]
    main_cv_role = [{'name': '曲红绡'}, {'name': '卫璃攸'}]
    supporting_cv = []
    supporting_cv_role = []
    commercial_drama = "商剧" if ori_price > 0 else "非商"
    with open("config_private.yaml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    notion_config = config.get("notion_config", {})
    database_id, token = (i for i in notion_config.values())

    notion_client = NotionClient(database_id, token, "fanjiao")
    notion_client.cre_in_database_paper(
        name, 
        description,
        description_sequel, 
        publish_date, 
        update_frequency, 
        ori_price, 
        author_name,
        main_cv,
        main_cv_role,
        supporting_cv,
        supporting_cv_role,
        commercial_drama
    )

if __name__ == "__main__":
    main()