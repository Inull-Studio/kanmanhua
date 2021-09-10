# coding=utf-8

from requests import get
from bs4 import BeautifulSoup
from urllib.parse import unquote

SEARCH_API = 'https://www.kanman.com/api/getsortlist'
CHAPTERINFO_API = 'https://www.kanman.com/api/getchapterinfov2'
KANMANHUA = 'https://www.kanman.com'
HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36 Edg/91.0.864.41'}


class KanManHua:
    def __init__(self):
        self.SEARCH_API = 'https://www.kanman.com/api/getsortlist'
        self.CHAPTERINFO_API = 'https://www.kanman.com/api/getchapterinfov2'
        self.KANMANHUA = 'https://www.kanman.com'
        self.HEADER = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36 Edg/91.0.864.41'}


def search(keyword: str):
    r = get(
        SEARCH_API, params={'search_key': keyword}, headers=HEADER)
    res = r.json()
    if res['message'] == 'ok':
        return r.json()['data'][0]['comic_id']


def get_chapter(comic_id):
    r = get(KANMANHUA+f'/{comic_id}', headers=HEADER)
    if r.status_code == 200:
        r.encoding = 'utf8'
        soup = BeautifulSoup(r.text, 'lxml')
        return soup.ol.li.a['href'].split('/')[-1].split('.')[0]


def chapter_info(chapter_id)


def get_img(chapter_id):
    pass


def download(img):
    pass


def main():
    get_chapter(27417)


if __name__ == '__main__':
    main()
