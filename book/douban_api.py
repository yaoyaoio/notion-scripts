import requests


def _get_image_from_douban(book_name: str) -> str:
    url = f'https://book.douban.com/j/subject_suggest?q={book_name}'
    headers = {
        "User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser;"
    }
    _resp = requests.get(url, headers=headers)
    if _resp.status_code != 200 or not _resp.json():
        return ""
    body = _resp.json()
    return body[0]["pic"]
