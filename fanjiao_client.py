import requests
import hashlib
import json
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Any
from dotenv import load_dotenv
import os
import logging

# 仅本地开发时加载 .env 文件（Docker 环境会跳过）
if os.getenv("ENV") != "production":
    load_dotenv()  # 默认加载 .env 文件


class FanjiaoSigner:
    """签名生成器"""

    _SALT = None  # 延迟加载

    @classmethod
    def get_salt(cls) -> str:
        """安全获取,优先从环境变量读取"""
        if not cls._SALT:
            # 从环境变量读取，不存在则使用开发默认值
            cls._SALT = os.getenv("FANJIAO_SALT")

            # 生产环境强制校验
            if os.getenv("ENV") == "production" and not os.getenv("FANJIAO_SALT"):
                raise RuntimeError("Missing FANJIAO_SALT in production environment")

        return cls._SALT

    @classmethod
    def generate(cls, query_params: str) -> str:
        raw_str = f"{query_params}{cls.get_salt()}"
        return hashlib.md5(raw_str.encode()).hexdigest()


class BaseFanjiaoAPI:
    """API客户端基类，封装通用逻辑"""

    _BASE_URL: str = None  # 由子类指定

    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Origin": "https://www.rela.me",
        }

    def _extract_album_id(self, url: str) -> str:
        """
        安全解析URL中的album_id参数
        :param url: 包含album_id参数的URL
        :raises ValueError: 当URL无效或缺少album_id时抛出
        """
        try:
            query = urlparse(url).query
            params = parse_qs(query)
            return params["album_id"][0]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid URL format: {url}") from e

    def _build_query(self, album_id: str) -> str:
        """由子类实现具体查询参数构造逻辑"""
        raise NotImplementedError

    def extract_relevant_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取关键数据"""
        raise NotImplementedError

    def _fetch_data(self, album_id: str) -> Dict[str, Any]:
        """执行API请求核心逻辑"""
        query = self._build_query(album_id)
        api_url = f"{self._BASE_URL}?{query}"

        headers = {**self.headers, "signature": FanjiaoSigner.generate(query)}

        try:
            response = self.session.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"API请求失败: {str(e)}") from e

    def fetch_album(self, url: str) -> Dict[str, Any]:
        """
        获取专辑数据
        :param url: 包含album_id参数的短链接
        :return: 解析后的JSON数据
        """
        album_id = self._extract_album_id(url)
        return self._fetch_data(album_id)


class FanjiaoAPI(BaseFanjiaoAPI):
    """音频数据API客户端"""

    _BASE_URL = None  # 延迟加载

    @classmethod
    def get_base_url(cls) -> str:
        """env方式读取"""
        if not cls._BASE_URL:
            cls._BASE_URL = os.getenv("FANJIAO_BASE_URL")
        return cls._BASE_URL

    def __init__(self):
        super().__init__()
        self.get_base_url()

    def _build_query(self, album_id: str) -> str:
        return f"album_id={album_id}&audio_id="

    def extract_relevant_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取关键数据"""
        return {
            "name": data["data"]["name"],
            "description": data["data"]["description"],
            "publish_date": data["data"]["publish_date"],
            "update_frequency": data["data"]["update_frequency"],
            "ori_price": data["data"]["ori_price"],
            "author_name": data["data"]["author_name"],
        }


class FanjiaoCVAPI(BaseFanjiaoAPI):
    """CV数据API客户端"""

    _BASE_URL = None  # 延迟加载

    @classmethod
    def get_base_url(cls) -> str:
        """env方式读取"""
        if not cls._BASE_URL:
            cls._BASE_URL = os.getenv("FANJIAO_CV_BASE_URL")
        return cls._BASE_URL

    def __init__(self):
        super().__init__()
        self.get_base_url()

    def _build_query(self, album_id: str) -> str:
        return f"album_id={album_id}&from=H5"

    def extract_relevant_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cv_list: List[Dict] = data.get("data", {}).get("cv_list", [])
        main_cv = []
        supporting_cv = []

        for cv in cv_list:
            entry = {"name": cv.get("name", ""), "role_name": cv.get("role_name", "")}
            if cv.get("cv_type") == 1:
                main_cv.append(entry)
            elif cv.get("cv_type") == 2:
                supporting_cv.append(entry)

        return {"main_cv": main_cv, "supporting_cv": supporting_cv}

    def extract_relevant_data_new(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cv_list: List[Dict] = data.get("data", {}).get("cv_list", [])

        process_entry = lambda cv: {
            "name": cv.get("name", ""),
            "role_name": cv.get("role_name", ""),
        }

        main_cv = list(
            map(process_entry, filter(lambda x: x.get("cv_type") == 1, cv_list))
        )
        supporting_cv = list(
            map(process_entry, filter(lambda x: x.get("cv_type") == 2, cv_list))
        )
        return {"main_cv": main_cv, "supporting_cv": supporting_cv}


def save_json(data: Dict, filename: str) -> None:
    """保存JSON数据到文件"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    """示例使用"""
    # test_urls = [
    #     "https://s.rela.me/c/1SqTNu?album_id=110750",
    #     "https://s.rela.me/c/1SqTNu?album_id=110838"
    # ]
    test_urls = ["https://s.rela.me/c/1SqTNu?album_id=110942"]  # 晴天

    fanjiao_api = FanjiaoAPI()
    fanjiao_cv_api = FanjiaoCVAPI()

    for url in test_urls:
        # try:
        album_id = parse_qs(urlparse(url).query)["album_id"][0]

        data = fanjiao_api.fetch_album(url)
        data_relevant = fanjiao_api.extract_relevant_data(data)
        save_json(data_relevant, f"data/data_{album_id}_relevant.json")
        print(f"专辑名称: {data_relevant['name']}")

        data_cv = fanjiao_cv_api.fetch_album(url)
        # save_json(data_cv, f"data/data_{album_id}_cv.json")
        data_cv_relevant = fanjiao_cv_api.extract_relevant_data(data_cv)
        save_json(data_cv_relevant, f"data/data_{album_id}_cv_relevant.json")
        print(f"CV姓名: {data_cv_relevant['main_cv']}")
        print("-" * 20)
    # except Exception as e:
    #     logging.error(f"处理 {url} 失败: {str(e)}")


if __name__ == "__main__":
    main()
