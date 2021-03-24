import requests
from bs4 import BeautifulSoup
import re
import datetime


class RepulserException(Exception):
    pass


class SiteError(RepulserException):
    pass


class Article:
    MONTH = {
        'января': '1',
        'февраля': '2',
        'марта': '3',
        'апреля': '4',
        'мая': '5',
        'июня': '6',
        'июля': '7',
        'августа': '8',
        'сентября': '9',
        'октября': '10',
        'ноября': '11',
        'декабря': '12',
    }

    def __init__(self):
        self.__header = ''
        self.__url = ''
        self.__datetime = datetime.datetime(datetime.MINYEAR, 1, 1)
        self.__tags = set()

    @property
    def header(self):
        return self.__header

    @header.setter
    def header(self, header: str):
        self.__header = header

    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, url: str):
        self.__url = url

    @property
    def date_time(self):
        return self.__datetime

    @date_time.setter
    def date_time(self, value):
        if isinstance(value, datetime.datetime):
            self.__datetime = value
        elif isinstance(value, str):
            dt_list = value.lower().split()
            if dt_list[0] == 'сегодня':
                self.__datetime = datetime.datetime.now()
                self.__datetime = self.__datetime.combine(self.__datetime, datetime.time.fromisoformat(dt_list[2]))
            elif dt_list[0] == 'вчера':
                self.__datetime = datetime.datetime.now()
                self.__datetime = self.__datetime.combine(self.__datetime, datetime.time.fromisoformat(dt_list[2]))
                self.__datetime = self.__datetime.replace(day=datetime.datetime.now().day-1)
            else:
                self.__datetime = self.__datetime.combine(self.__datetime, datetime.time.fromisoformat(dt_list[4]))
                self.__datetime = self.__datetime.replace(day=int(dt_list[0]), month=int(self.MONTH[dt_list[1]]),
                                                          year=int(dt_list[2]))

    @property
    def tags(self):
        return self.__tags.copy()

    @tags.setter
    def tags(self, value):
        self.__tags = set(value)

    def add_tag(self, value: str):
        self.__tags.add(value.lower())


class Parser:
    def __init__(self, blog_url: str):
        self.url = blog_url
        self.articles = list()
        self.parse_datetime = datetime.datetime(datetime.MINYEAR, 1, 1)

    def set_url(self, url: str):
        self.url = url

    @staticmethod
    def __has_id_post(id_):
        return id_ and re.compile("post_").search(id_)

    def parse(self, url=''):
        self.url = url or self.url

        r = requests.get(self.url)
        if r.status_code != 200:
            raise SiteError(f'Site error: {r.status_code}')

        self.articles = []
        self.parse_datetime = datetime.datetime.now()

        soup = BeautifulSoup(r.content, 'lxml')

        p_articles = soup.find_all('li', id=self.__has_id_post)

        for p_artcl in p_articles:
            post = Article()
            header = p_artcl.find('h2')
            post.header = header.find('a').getText()
            post.date_time = p_artcl.find('span', class_="post__time").getText()
            post.url = header.a['href']

            tags = p_artcl.find_all('li', class_="inline-list__item inline-list__item_hub")
            for tag in tags:
                post.add_tag(tag.find('a').getText())

            self.articles.append(post)

    def get_by_filter(self, dt: datetime.datetime, tags):
        res = list()
        for elem in self.articles:
            if (elem.date_time >= dt) and (elem.tags in set(tags)):
                res.append(elem)
        return res

    def get_all(self):
        return self.articles.copy()

    def get_parse_datetime(self):
        return self.parse_datetime


class Config:
    pass
