# coding=utf-8

from requests import get
from bs4 import BeautifulSoup
from urllib.parse import unquote
from json import loads
from os import chdir, mkdir, getcwd, path
from tempfile import mktemp, gettempdir
from shutil import move
from threading import Thread

from sys import argv

# time.strptime('2021-09-11T09:47:50.000Z', '%Y-%m-%dT%H:%M:%S.000Z')


class KanManHua():
    def __init__(self, proxy=False):
        super(KanManHua, self).__init__()
        self.SRC = path.dirname(__file__)
        self.SEARCH_API = 'https://www.kanman.com/api/getsortlist'
        self.CHAPTERINFO_API = 'https://www.kanman.com/api/getchapterinfov2'
        self.KANMANHUA = 'https://www.kanman.com'
        self.HEADER = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36 Edg/91.0.864.41'}
        if proxy:
            print('proxy On')
            self.proxies = {'http': 'http://127.0.0.1:2802'}
        else:
            print('proxy Off')
            self.proxies = {}

    def _search(self, keyword):
        try:
            r = get(
                self.SEARCH_API, params={'search_key': keyword}, headers=self.HEADER, proxies=self.proxies)
            res = r.json()
            if res['message'] == 'ok':
                res = r.json()['data']
                if not res:
                    print('无搜索结果')
                    return
                if len(res) > 1:
                    for i in range(len(res)):
                        print(
                            'id:', i+1, '\t', res[i]['comic_name'])
                    print('请输入要爬取的漫画id:', end='')
                    i = int(input())
                    if i-1 in range(len(res)):
                        self.comic_id = res[i-1]['comic_id']
                else:
                    self.comic_id = res[0]['comic_id']
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
            print('获取chapterid成功')

    def _chapter_info(self, comic_id, chapter_newid: str):
        r = get(self.CHAPTERINFO_API, params={
                'comic_id': comic_id, 'chapter_newid': chapter_newid, 'quality': 'middle'}, headers=self.HEADER, proxies=self.proxies)
        r.encoding = 'utf8'
        res = r.text
        res = unquote(res)
        res = loads(res)
        if res['message'] == 'ok':
            self.chapter_info = res

    def _last_chapter_info(self):
        self._chapter_info(
            self.comic_id, self.chapter_info['data']['last_chapter_newid'])

    def _next_chapter_info(self):
        chapter_newid = self.chapter_info['data']['next_chapter']['chapter_newid']
        self._chapter_info(self.comic_id, chapter_newid)

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

    def _download(self, img_url: str, chapter_name: str):
        try:
            if path.exists(path.join(self.SRC, 'downloads', self.comic_name, chapter_name, img_url.split('/')[-1].split('-')[0])):
                return
            r = get(img_url, headers=self.HEADER, proxies=self.proxies)
            print(
                '正在下载:', self.comic_name, chapter_name, img_url.split('/')[-1].split('-')[0])
            filename = mktemp()
            f = open(filename, 'wb')
            f.write(r.content)
            f.close()
            move(filename, path.join(
                self.SRC, 'downloads', self.comic_name, chapter_name, img_url.split('/')[-1].split('-')[0]))
        except Exception as e:
            print(e)

    def _is_next_chapter(self):
        return True if self.chapter_info['data']['next_chapter'] else False


def main():
    try:
        kanman = KanManHua()
        kanman._search('噬龙蚁')
        kanman._get_first_chapter_id()
        kanman._chapter_info(kanman.comic_id, kanman.chapter_newid)
        while kanman._is_next_chapter():
            tlist = []
            kanman._get_imgs()
            for img in kanman.images[0]:
                t = Thread(
                    target=kanman._download, args=(img, kanman.images[1]))
                t.setDaemon(True)
                tlist.append(t)
                # kanman._download(img, kanman.images[1])
            for t in tlist:
                t.start()
            for t in tlist:
                t.join()
            kanman._next_chapter_info()
        print(kanman.comic_name, '下载完成')
    except KeyboardInterrupt:
        exit(0)


if __name__ == '__main__':
    main()
