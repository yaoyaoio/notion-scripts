import abc
import os
import dataclasses
from typing import Dict, List, Optional, Union


@dataclasses.dataclass
class MetaSourceInfo:
    id: str
    description: str
    link: str


@dataclasses.dataclass
class MetaRecord:
    id: Union[str, int]
    # 名称
    title: str
    # 作者
    authors: List[str]
    # 地址
    url: str
    # 来源
    source: MetaSourceInfo
    # 封面
    cover: str = os.path.join("", 'generic_cover.jpg')
    series: Optional[str] = None
    series_index: Optional[Union[int, float]] = 0
    identifiers: Dict[str, Union[str, int]] = dataclasses.field(default_factory=dict)
    # 出版社
    publisher: Optional[str] = None
    # 出版日期
    publishedDate: Optional[str] = None
    # 评分
    rating: Optional[int] = 0
    # 语言
    languages: Optional[List[str]] = dataclasses.field(default_factory=list)
    # 标签
    tags: Optional[List[str]] = dataclasses.field(default_factory=list)
    # 简介
    description: Optional[str] = ""


class Metadata:
    __name__ = "Generic"
    __id__ = "generic"

    def __init__(self):
        self.active = True

    def set_status(self, state):
        self.active = state

    @abc.abstractmethod
    def search(
            self, query: str, generic_cover: str = "", locale: str = "cn"
    ) -> Optional[List[MetaRecord]]:
        pass

    @abc.abstractmethod
    def search_one(
            self, query: str, generic_cover: str = "", locale: str = "cn"
    ) -> Optional[MetaRecord]:
        pass
