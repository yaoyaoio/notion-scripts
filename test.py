from lxml import etree
from book.douban import DEFAULT_HEADERS, DoubanBookHtmlParser
import requests

if __name__ == "__main__":
    paser = DoubanBookHtmlParser()
    resp = requests.get("https://book.douban.com/subject/35934902/", headers=DEFAULT_HEADERS)
    content = resp.content
    paser.parse_book(url="https://book.douban.com/subject/35934902/", content=content.decode("utf-8"))
