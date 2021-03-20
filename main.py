import requests
from bs4 import BeautifulSoup
import re


def has_id_post(id):
    return id and re.compile('post_').search(id)


def main():
    r = requests.get('https://habr.com/ru/company/skillfactory/blog/')
    soup = BeautifulSoup(r.content, 'lxml')

    articles = soup.find_all('li', id=has_id_post)

    for artcl in articles:
        header = artcl.find('h2')
        print()
        print()
        print(header.find('a').getText())
        print(artcl.find('span', class_="post__time").getText())
        print(header.a['href'])
        print()

        tags = artcl.find_all('li', class_="inline-list__item inline-list__item_hub")

        for tag in tags:
            print(tag.find('a').getText())


if __name__ == '__main__':
    main()
