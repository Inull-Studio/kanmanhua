# coding: utf-8
from requests import get
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
        self.COMICINFO_API = 'https://www.kanman.com/api/getcomicinfo_body'
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

    def get_comic_info(self):
        r = get(self.COMICINFO_API, params={'comic_id': self.comic_id})
        r.encoding = 'utf8'
        res = r.json()
        if res['message'] == 'ok':
            self.chapters = res['data']['comic_chapter']
            self.chapters.reverse()

    def _chapter_info(self, comic_id, chapter_newid: str):
        r = get(self.CHAPTERINFO_API, params={
                'comic_id': comic_id, 'chapter_newid': chapter_newid, 'quality': 'high'}, headers=self.HEADER, proxies=self.proxies)
        r.encoding = 'utf8'
        res = loads(unquote(r.text))
        if res['message'] == 'ok':
            self.chapter_info = res

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


def main():
    try:
        kanman = KanManHua()
        if kanman._search(argv[1]):
            kanman.get_comic_info()
            for chapter in kanman.chapters:
                results = []
                kanman._chapter_info(kanman.comic_id, chapter['chapter_id'])
                kanman._get_imgs()
                with ThreadPoolExecutor(max_workers=8) as execute:
                    for img in kanman.images[0]:
                        res = execute.submit(kanman._download, img, kanman.images[1])
                        results.append(res)
                    for r in track(results, description='正在下载{}...'.format(chapter['chapter_name'])):
                        r.result()
            print(kanman.comic_name, '下载完成')
    except KeyboardInterrupt:
        exit(0)


if __name__ == '__main__':
    if len(argv) == 2:
        main()
    else:
        print('帮助:', argv[0], '<漫画名>')
