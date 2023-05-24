from lxml import etree
from movie.douban import DEFAULT_HEADERS, DoubanaMovieProvider
import requests


def test_date_parse():
    import re

    s = "1994-09-10(多伦多电影节)"
    match = re.search(r'\d{4}-\d{2}-\d{2}', s)
    if match:
        date = match.group()


if __name__ == "__main__":
    provider = DoubanaMovieProvider()
    provider.search("tt0111161")
    test_date_parse()
