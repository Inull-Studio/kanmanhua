# coding=utf-8

from requests import get
from bs4 import BeautifulSoup
from urllib.parse import unquote
from json import loads
import cv2
from os import chdir, mkdir, getcwd, path
from tempfile import mktemp, gettempdir
from shutil import move

SRC = getcwd()
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


def chapter_info(comic_id, chapter_id):
    r = get(CHAPTERINFO_API, params={
            'comic_id': comic_id, 'chapter_newid': chapter_id, 'quality': 'middle'}, headers=HEADER)
    r.encoding = 'utf8'
    res = r.text
    res = unquote(res)
    res = loads(res)
    if res['message'] == 'ok':
        return res


def next_chapter_info(chapter_info: dict):
    chapter_id = chapter_info['data']['next_chapter']['chapter_newid']
    comic_id = chapter_info['data']['comic_id']
    r = get(CHAPTERINFO_API, params={
            'comic_id': comic_id, 'chapter_newid': chapter_id, 'quality': 'middle'}, headers=HEADER)
    r.encoding = 'utf8'
    res = r.text
    res = unquote(res)
    res = loads(res)
    if res['message'] == 'ok':
        return res


def get_imgs(chapter_info: dict):
    if not path.exists(path.join(SRC, 'downloads', chapter_info['data']['current_chapter']['chapter_name'])):
        mkdir(path.join(
            SRC, 'downloads', chapter_info['data']['current_chapter']['chapter_name']))
    return chapter_info['data']['current_chapter']['chapter_img_list'], chapter_info['data']['current_chapter']['chapter_name']


def download(img_url: str, chapter_name: str):
    try:
        if not path.exists('downloads'):
            mkdir('downloads')
        r = get(img_url, headers=HEADER)
        filename = mktemp()
        f = open(filename, 'wb')
        f.write(r.content)
        f.close()
        move(filename, path.join(
            SRC, 'downloads', chapter_name, img_url.split('/')[-1].split('-')[0]))
        # chdir(gettempdir())
        # img = cv2.imread(filename)
        # cv2.imshow('1', img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
    except Exception as e:
        print(e)


def main():
    detail = get_imgs(chapter_info(27417, 'dyhzs'))
    for img in detail[0]:
        download(img, detail[1])


if __name__ == '__main__':
    main()
