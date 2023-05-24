import os
import dataclasses
from book import DoubanBookProvider, MetaRecord
from movie import DoubanaMovieProvider, MovieMetaRecord
from notion_client import Client as NotionClient
from typing import List, Dict, Any

BOOK_DATABASE_ID = ""  # 读书笔记对应到数据库id
MOVIE_DATABASE_ID = ""
NOTION_TOKEN = ""  # 自己的integrations的token


@dataclasses.dataclass
class BookEmptyPage:
    page_id: str
    book_name: str
    isbn: str


@dataclasses.dataclass
class MovieEmptyPage:
    page_id: str
    movie_name: str
    imdb: str


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


def gen_movie_properties(meta: MovieMetaRecord) -> Dict[Any, Any]:
    return {
        "properties": {
            "封面": {
                "files": [{
                    "name": meta.title,
                    "type": "external",
                    "external": {
                        "url": meta.cover
                    }
                }]
            },
            "主演": {
                "multi_select": [{"name": actor} for
                                 actor in meta.actors]
            },
            "导演": {
                "multi_select": [{"name": director} for
                                 director in meta.directors]
            },

            "国家": {
                "multi_select": [{"name": meta.countries}]
            },
            "标签": {
                "multi_select": [
                    {"name": tag}
                    for tag in meta.tags]
            },
            "上映日期": {
                "type": "date",
                "date": {
                    "start": meta.release_date,
                    "end": None,
                    "time_zone": None,
                }
            }
        }
    }


def sync_movie_info(movies: List[MovieEmptyPage], provider: DoubanaMovieProvider, nc: NotionClient) -> int:
    for movie in movies:
        try:
            movie_mata_record = provider.search_one(query=movie.imdb)
            properties = gen_movie_properties(movie_mata_record)
            nc.pages.update(page_id=movie.page_id, **properties)
            print(f"Synced {movie.movie_name}")
        except Exception as e:
            print(f"Failed to sync {movie.movie_name}, error: {e}")
    return len(movies)


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


def sync_movie(database_id: str, c: NotionClient):
    movie_provider = DoubanaMovieProvider()
    query_filter = {
        "property": "封面",  # 封面列的名称
        "files": {
            "is_empty": True
        }
    }
    page_properites = c.databases.query(database_id=database_id, filter=query_filter)
    results = page_properites["results"]
    movies_incomplete = [MovieEmptyPage(
        page_id=item["id"],
        movie_name=item["properties"]["Name"]["title"][0]["text"]["content"],
        imdb=item["properties"]["IMDb"]["rich_text"][0]["plain_text"]) for
        item in results]
    print(movies_incomplete)
    sync_movie_info(movies_incomplete, movie_provider, c)


def sync_book(database_id: str, c: NotionClient):
    book_provider = DoubanBookProvider()
    query_filter = {
        "property": "Cover",  # 封面列的名称
        "files": {
            "is_empty": True
        }
    }
    page_properites = c.databases.query(database_id=database_id, filter=query_filter)
    results = page_properites["results"]
    books_incomplete = [BookEmptyPage(
        page_id=item["id"],
        book_name=item["properties"]["书名"]["title"][0]["text"]["content"],
        isbn=item["properties"]["ISBN"]["number"]) for
        item in results]
    sync_book_info(books_incomplete, book_provider, c)


if __name__ == '__main__':
    MOVIE_DATABASE_ID = os.environ["MOVIE_DATABASE_ID"]
    client = NotionClient(auth=os.environ["NOTION_TOKEN"])
    sync_movie(MOVIE_DATABASE_ID, client)
