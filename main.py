import configparser

import classes


def main():

    sf_habr = classes.Parser('https://habr.com/ru/company/skillfactory/blog/')

    sf_habr.parse()

    for post in sf_habr.get_all():
        print()
        print()
        print(post.header)
        print(post.url)
        print(post.date_time)
        print(post.tags)


if __name__ == '__main__':
    main()
