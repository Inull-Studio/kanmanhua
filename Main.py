# coding=utf-8
from requests import get
from bs4 import BeautifulSoup
from urllib.parse import unquote
from urllib.request import getproxies
from json import loads
from os import mkdir, path
from tempfile import mktemp
from shutil import move
from rich.progress import track
from rich import print
from concurrent.futures import ThreadPoolExecutor
from sys import argv


class KanManHua():
    def __init__(self, proxy=getproxies()):
        super(KanManHua, self).__init__()
        self.SRC = path.dirname(__file__)
        self.SEARCH_API = 'https://www.kanman.com/api/getsortlist'
        self.CHAPTERINFO_API = 'https://www.kanman.com/api/getchapterinfov2'
        self.KANMANHUA = 'https://www.kanman.com'
        self.HEADER = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36 Edg/91.0.864.41',
            'Referer': 'https://www.kanman.com/'
        }
        if proxy:
            print('proxy On')
        else:
            print('proxy Off')
        self.proxies = proxy

    def _search(self, keyword):
        try:
            r = get(
                self.SEARCH_API, params={'search_key': keyword}, headers=self.HEADER, proxies=self.proxies)
            res = r.json()
            if res['message'] == 'ok':
                res = r.json()['data']
                if not res:
                    print('无搜索结果')
                    return False
                if len(res) > 1:
                    for i in range(len(res)):
                        print(
                            'id:', i+1, '\t', res[i]['comic_name'])
                    i = int(input('请输入要爬取的漫画id:'))
                    if i-1 in range(len(res)):
                        self.comic_id = res[i-1]['comic_id']
                        return True
                else:
                    self.comic_id = res[0]['comic_id']
                    return True
        except Exception as e:
            print(e)

    def _get_first_chapter_id(self):
        r = get(self.KANMANHUA+f'/{self.comic_id}',
                headers=self.HEADER, proxies=self.proxies)
        if r.status_code == 200:
            r.encoding = 'utf8'
            soup = BeautifulSoup(r.text, 'lxml')
            self.chapter_newid = soup.ol.li.a['href'].split(
                '/')[-1].split('.')[0]
            print('获取chapterid成功', self.chapter_newid)

    def _chapter_info(self, comic_id, chapter_newid: str):
        r = get(self.CHAPTERINFO_API, params={
                'comic_id': comic_id, 'chapter_newid': chapter_newid, 'quality': 'high'}, headers=self.HEADER, proxies=self.proxies)
        r.encoding = 'utf8'
        res = loads(unquote(r.text))
        if res['message'] == 'ok':
            self.chapter_info = res

    def _last_chapter_info(self):
        self._chapter_info(
            self.comic_id, self.chapter_info['data']['last_chapter_newid'])

    def _next_chapter_info(self):
        self._chapter_info(
            self.comic_id, self.chapter_info['data']['next_chapter']['chapter_newid'])

    def _get_imgs(self):
        if not path.exists('downloads'):
            mkdir('downloads')
        self.comic_name = self.chapter_info['data']['comic_name']
        sets = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '.']
        chapter_name = self.chapter_info['data']['current_chapter']['chapter_name'].strip(
        )
        for char in chapter_name:
            if char in sets:
                chapter_name = chapter_name.replace(char, '')
        if not path.exists(path.join(self.SRC, 'downloads', self.comic_name, chapter_name)):
            if not path.exists(path.join(self.SRC, 'downloads', self.comic_name)):
                mkdir(path.join(self.SRC, 'downloads', self.comic_name))
            mkdir(path.join(self.SRC, 'downloads', self.comic_name, chapter_name))
        self.images = self.chapter_info['data']['current_chapter']['chapter_img_list'], chapter_name
        self.down_chapter_name = chapter_name

    def _download(self, img_url: str, chapter_name: str):
        try:
            if path.exists(path.join(self.SRC, 'downloads', self.comic_name, chapter_name, img_url.split('/')[-1].split('-')[0])):
                return
            r = get(img_url, headers=self.HEADER, proxies=self.proxies)
            # print('正在下载:', self.comic_name, chapter_name, img_url.split('/')[-1].split('-')[0])
            filename = mktemp()
            f = open(filename, 'wb')
            f.write(r.content)
            f.close()
            move(filename, path.join(
                self.SRC, 'downloads', self.comic_name, chapter_name, img_url.split('/')[-1].split('-')[0]))
            return True
        except Exception as e:
            print(e)

    def _is_next_chapter(self) -> bool:
        return True if self.chapter_info['data']['next_chapter'] else False

    def _is_prev_chapter(self) -> bool:
        return True if self.chapter_info['data']['prev_chapter'] else False


def main():
    try:
        kanman = KanManHua()
        if kanman._search(argv[1]):
            kanman._get_first_chapter_id()
            kanman._chapter_info(kanman.comic_id, kanman.chapter_newid)
            kanman._get_imgs()
            for img in track(kanman.images[0], description=f'正在下载{kanman.images[1]}...'):
                kanman._download(img, kanman.images[1])
            while kanman._is_next_chapter():
                results = []
                kanman._next_chapter_info()
                kanman._get_imgs()
                with ThreadPoolExecutor(max_workers=8) as execute:
                    for img in kanman.images[0]:
                        res = execute.submit(kanman._download, img, kanman.images[1])
                        results.append(res)
                    for r in track(results, description=f'正在下载{kanman.images[1]}...'):
                        r.result()
            print(kanman.comic_name, '下载完成')
    except KeyboardInterrupt:
        exit(0)


if __name__ == '__main__':
    if len(argv) == 2:
        main()
    else:
        print('帮助:', argv[0], '<漫画名>')
