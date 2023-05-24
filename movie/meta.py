import abc
import os
import dataclasses
from typing import Dict, List, Optional, Union


@dataclasses.dataclass
class MovieMetaSourceInfo:
    id: str
    description: str
    link: str


@dataclasses.dataclass
class MovieMetaRecord:
    movie_id: Union[str, int]
    # 名称
    title: str
    # 导演
    directors: List[str]
    # 演员
    actors: List[str]
    # 地址
    url: str
    # 来源
    source: MovieMetaSourceInfo
    # 封面
    cover: str = os.path.join("", 'generic_cover.jpg')
    # 标识
    identifiers: Dict[str, Union[str, int]] = dataclasses.field(default_factory=dict)
    # 互联网电影数据库
    imdb: Optional[str] = None
    # 国家
    countries: Optional[str] = None
    # 上映日期
    release_date: Optional[str] = None
    # 评分
    rating: Optional[int] = 0
    # 语言
    languages: Optional[List[str]] = dataclasses.field(default_factory=list)
    # 标签
    tags: Optional[List[str]] = dataclasses.field(default_factory=list)
    # 简介
    description: Optional[str] = ""


class MetadataProvider:
    __name__ = "Generic Metadata Provider"
    __id__ = "generic"

    def __init__(self):
        pass

    @abc.abstractmethod
    def search(
            self, query: str, generic_cover: str = "", locale: str = "cn"
    ) -> Optional[List[MovieMetaRecord]]:
        pass

    @abc.abstractmethod
    def search_one(
            self, query: str, generic_cover: str = "", locale: str = "cn"
    ) -> Optional[MovieMetaRecord]:
        pass
