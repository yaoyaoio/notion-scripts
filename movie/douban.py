import random
import re
import time
import requests
from datetime import datetime
from typing import List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, unquote
from functools import lru_cache
from lxml import etree
from movie.meta import MovieMetaSourceInfo, MovieMetaRecord, MetadataProvider

DOUBAN_SEARCH_JSON_URL = "https://www.douban.com/j/search"  # 最新豆瓣屏蔽此url
DOUBAN_SEARCH_URL = "https://www.douban.com/search"
DOUBAN_MOVIE_CAT = "1002"
DOUBAN_MOVIE_CACHE_SIZE = 500  # 最大缓存数量
DOUBAN_CONCURRENCY_SIZE = 5  # 并发查询数
DOUBAN_MOVIE_URL_PATTERN = re.compile(".*/subject/(\\d+)/?")
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3573.0 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate'
}

__ALL__ = ["DoubanaMovieProvider"]


class DoubanaMovieProvider(MetadataProvider):

    def __init__(self):
        self.searcher = DoubanMovieSearcher()
        super().__init__()

    def search(
            self, query: str, generic_cover: str = "", locale: str = "en"
    ) -> Optional[List[MovieMetaRecord]]:
        return self.searcher.search_movies(query)

    def search_one(
            self, query: str, generic_cover: str = "", locale: str = "en"
    ) -> Optional[MovieMetaRecord]:
        resp = self.searcher.search_movies(query)
        if resp:
            return resp[0]


class DoubanMovieSearcher:

    def __init__(self):
        self.movie_loader = DoubanMovieLoader()
        self.thread_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix='douban_movie_async')

    def search_movies(self, query: str) -> List[Any]:
        movie_urls = self.load_movie_urls(query)
        movies = []
        futures = [self.thread_pool.submit(self.movie_loader.load_movie, movie_url) for movie_url in movie_urls]
        for future in as_completed(futures):
            movie = future.result()
            if movie is not None:
                movies.append(future.result())
        return movies

    @staticmethod
    def calc_url(href: str) -> str:
        query = urlparse(href).query
        params = {item.split('=')[0]: item.split('=')[1] for item in query.split('&')}
        url = unquote(params['url'])
        if DOUBAN_MOVIE_URL_PATTERN.match(url):
            return url

    def load_movie_urls(self, query: str) -> List[Any]:
        url = DOUBAN_SEARCH_URL
        params = {"cat": DOUBAN_MOVIE_CAT, "q": query}
        res = requests.get(url, params, headers=DEFAULT_HEADERS)
        movie_urls = []
        if res.status_code in [200, 201]:
            html = etree.HTML(res.content)
            alist = html.xpath('//a[@class="nbg"]')
            for link in alist:
                href = link.attrib['href']
                parsed = self.calc_url(href)
                if parsed:
                    if len(movie_urls) < DOUBAN_CONCURRENCY_SIZE:
                        movie_urls.append(parsed)
        return movie_urls


class DoubanMovieLoader:

    def __init__(self):
        self.movie_parser = DoubanMovieHtmlParser()

    @lru_cache(maxsize=DOUBAN_MOVIE_CACHE_SIZE)
    def load_movie(self, url):
        movie = None
        self.random_sleep()
        start_time = time.time()
        res = requests.get(url, headers=DEFAULT_HEADERS)
        if res.status_code in [200, 201]:
            print("Download Movie:{} success,耗时 {:.0f}ms".format(url, (time.time() - start_time) * 1000))
            movie_detail_content = res.content
            movie = self.movie_parser.parse_movie(url, movie_detail_content)
        return movie

    @staticmethod
    def random_sleep():
        random_sec = random.random() / 10
        print("Random sleep time {}s".format(random_sec))
        time.sleep(random_sec)


class DoubanMovieHtmlParser:
    def __init__(self):
        self.id_pattern = DOUBAN_MOVIE_URL_PATTERN
        self.date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
        self.tag_pattern = re.compile("criteria = '(.+)'")

    def parse_movie(self, url, content) -> MovieMetaRecord:
        movie = MovieMetaRecord(
            movie_id="",
            title="",
            actors=[],
            directors=[],
            description="",
            url="",
            source=MovieMetaSourceInfo("", "", "")
        )
        html = etree.HTML(content)
        if html is None:
            return movie
        title_element = html.xpath("//span[@property='v:itemreviewed']")
        movie.title = self.__get_text(title_element)
        share_element = html.xpath("//a[@data-url]")
        if len(share_element):
            url = share_element[0].attrib['data-url']
        movie.url = url
        id_match = self.id_pattern.match(url)
        if id_match:
            movie.movie_id = id_match.group(1)
        img_element = html.xpath("//a[@class='nbg']")
        if len(img_element):
            cover = img_element[0].attrib['href']
            if not cover or cover.endswith('update_image'):
                movie.cover = ''
            else:
                movie.cover = cover
        elements = html.xpath("//span[@class='pl']")
        for element in elements:
            text = self.__get_text(element)
            if text.startswith("导演"):
                movie.directors.extend([self.__get_text(director_element) for director_element in
                                        filter(self.director_filter, element.findall("..//a"))])
            elif text.startswith("主演"):
                movie.actors.extend([self.__get_text(actor_element) for actor_element in
                                     filter(self.actor_filter, element.findall("..//a"))])
            elif text.startswith("类型"):
                movie.genres = self.__get_text(element.getnext())
            elif text.startswith("制片国家/地区"):
                movie.countries = self.__get_tail(element)
            elif text.startswith("IMDb"):
                movie.identifiers["imdb"] = self.__get_tail(element)
                movie.imdb = self.__get_tail(element)
            elif text.startswith("语言"):
                movie.languages = self.__get_tail(element)
            elif text.startswith("上映日期"):
                movie.release_date = self.__get_release_date(self.__get_tail(element))
        summary_element = html.xpath("//div[@id='link-report']//div[@class='intro']")
        if len(summary_element):
            movie.description = etree.tostring(summary_element[-1], encoding="utf8").decode("utf8").strip()
        tag_elements = html.xpath("//a[contains(@class, 'tag')]")
        if len(tag_elements):
            movie.tags = [self.__get_text(tag_element) for tag_element in tag_elements]
        else:
            movie.tags = self.__get_tags(content)
        print(movie)
        return movie

    def __get_tags(self, movie_content) -> List[Any]:
        tag_match = self.tag_pattern.findall(movie_content.decode('utf-8'))
        if len(tag_match):
            return [tag.replace('7:', '') for tag in
                    filter(lambda tag: tag and tag.startswith('7:'), tag_match[0].split('|'))]
        return []

    def __get_release_date(self, date_str):
        if date_str:
            date_match = self.date_pattern.search(date_str)
            if date_match:
                date_str = date_match.group()
                date_time = datetime.strptime(date_str, "%Y-%m-%d")
                iso8601_date = date_time.date().isoformat()
                return iso8601_date
        return date_str

    def __get_rating(self, rating_element) -> float:
        return float(self.__get_text(rating_element, '0')) / 2

    @staticmethod
    def author_filter(a_element):
        a_href = a_element.attrib['href']
        return '/author' in a_href or '/search' in a_href

    @staticmethod
    def director_filter(a_element):
        a_href = a_element.attrib['href']
        return '/celebrity' in a_href or '/search' in a_href

    @staticmethod
    def actor_filter(a_element):
        a_href = a_element.attrib['href']
        return '/celebrity' in a_href or '/search' in a_href

    @staticmethod
    def __get_text(element, default_str=''):
        text = default_str
        if len(element) and element[0].text:
            text = element[0].text.strip()
        elif isinstance(element, etree._Element) and element.text:
            text = element.text.strip()
        return text if text else default_str

    def __get_tail(self, element, default_str=''):
        text = default_str
        if isinstance(element, etree._Element) and element.tail:
            text = element.tail.strip()
            if not text:
                text = self.__get_text(element.getnext(), default_str)
        return text if text else default_str
