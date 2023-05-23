import os
import dataclasses
from book import DoubanBookProvider, MetaRecord
from notion_client import Client as NotionClient
from typing import List, Dict, Any

DATABASE_ID = ""  # 读书笔记对应到数据库id
NOTION_TOKEN = ""  # 自己的integrations的token


@dataclasses.dataclass
class BookEmptyPage:
    page_id: str
    book_name: str
    isbn: str


def gen_book_properties(meta: MetaRecord) -> Dict[Any, Any]:
    return {
        "properties": {
            "Cover": {
                "files": [{
                    "name": meta.title,
                    "type": "external",
                    "external": {
                        "url": meta.cover
                    }
                }]
            },
            "Authors": {
                "multi_select": [{"name": author} for
                                 author in meta.authors]
            },
            "Publisher": {
                "select": {
                    "name": meta.publisher
                }
            },
            "Tags": {
                "multi_select": [
                    {"name": tag}
                    for tag in meta.tags]
            },
            "PublishedDate": {
                "type": "date",
                "date": {
                    "start": meta.publishedDate,
                    "end": None,
                    "time_zone": None,
                }
            }
        }
    }


def sync_book_info(books: List[BookEmptyPage], provider: DoubanBookProvider, nc: NotionClient) -> int:
    for book in books:
        try:
            book_mata_record = provider.search_one(query=book.isbn)
            properties = gen_book_properties(book_mata_record)
            nc.pages.update(page_id=book.page_id, **properties)
            print(f"Synced {book.book_name}")
        except Exception as e:
            print(f"Failed to sync {book.book_name}, error: {e}")
    return len(books)


if __name__ == '__main__':
    book_provider = DoubanBookProvider()
    DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
    client = NotionClient(auth=os.environ["NOTION_TOKEN"])
    query_filter = {
        "property": "Cover",  # 封面列的名称
        "files": {
            "is_empty": True
        }
    }
    page_properites = client.databases.query(database_id=DATABASE_ID, filter=query_filter)
    results = page_properites["results"]
    books_incomplete = [BookEmptyPage(
        page_id=item["id"],
        book_name=item["properties"]["书名"]["title"][0]["text"]["content"],
        isbn=item["properties"]["ISBN"]["number"]) for
        item in results]
    sync_book_info(books_incomplete, book_provider, client)
