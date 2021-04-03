import configparser
import time
import datetime

import classes

CONFIG_FILE_NAME = 'config.ini'


def main():

    config = config_read(CONFIG_FILE_NAME)

    if config[SECTION][SEND_PERIOD]:
        try:
            days = int(config[SECTION][SEND_PERIOD])
        except ValueError as err:
            raise classes.ConfigError(err, f'{SEND_PERIOD} должен быть целым числом.')
        send_period = datetime.timedelta(days=days)

        if config[SECTION][SEND_TIME]:
            try:
                send_time = datetime.time.fromisoformat(config[SECTION][SEND_TIME])
            except ValueError as err:
                raise classes.ConfigError(err, f'{SEND_TIME} должен быть в формате'
                                               f' HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]].')
        else:
            send_time = datetime.datetime.now().time()

        if config[SECTION][LAST_SEND]:
            try:
                last_send = datetime.datetime.fromisoformat(config[SECTION][LAST_SEND])
            except ValueError as err:
                raise classes.ConfigError(err, f'{LAST_SEND} должен быть в формате '
                                               f'YYYY-MM-DD[*HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]]]')
        else:
            last_send = datetime.datetime.now() - send_period

        waiting_time = datetime.datetime.combine((last_send + send_period).date(), send_time) - datetime.datetime.now()

        if waiting_time.total_seconds() < 0:
            waiting_time = datetime.datetime.combine(datetime.date.today(), send_time) - datetime.datetime.now()
            if waiting_time.total_seconds() < 0:
                waiting_time = datetime.datetime.combine(datetime.date.today(), send_time)\
                                   .replace(day=datetime.date.today().day+1) - datetime.datetime.now()
    else:
        try:
            poll_period = datetime.timedelta(minutes=int(config[SECTION][POLL_PERIOD]))
        except ValueError as err:
            raise classes.ConfigError(err, f'{POLL_PERIOD} должен быть целым числом.')
        waiting_time = poll_period
        send_period = datetime.timedelta(days=1)
        last_send = datetime.datetime.now() - waiting_time

    print(waiting_time.total_seconds())

    bot = classes.SlackBot(config[SECTION][BOT_TOKEN])

    sf_habr = classes.Parser(config[SECTION][HABR_BLOG])

    while True:
        print(datetime.datetime.now().isoformat())
        time.sleep(waiting_time.total_seconds())
        print(datetime.datetime.now().isoformat())

        sf_habr.parse(days=send_period.days)
        for post in sf_habr.get_all():
            print()
            print()
            print(post.header)
            print(post.url)
            print(post.date_time)
            print(post.tags)

        print(f'last_send {last_send}')
        print(config[SECTION][TAGS])
        bot.post_in_channel(config[SECTION][CHANNEL], config[SECTION][TEXT],
                            sf_habr.get_by_filter(last_send, get_tags(config[SECTION][TAGS])))
        last_send = sf_habr.parse_datetime
        if config[SECTION][SEND_PERIOD]:
            waiting_time = datetime.datetime.combine((last_send + send_period).date(), send_time)\
                           - datetime.datetime.now()
            config[SECTION][LAST_SEND] = last_send.isoformat()
            config_write(config, CONFIG_FILE_NAME)
        else:
            waiting_time = poll_period
        print(f'new poll: {waiting_time.total_seconds()}')


def get_tags(string: str):
    return {tg.strip().lower() for tg in string.split(',')}

SECTION = 'options'
HABR_BLOG = 'habr_blog'
POLL_PERIOD = 'poll_period'
BOT_TOKEN = 'bot_token'
CHANNEL = 'channel'
TEXT = 'message_text'
TAGS = 'tags'
SEND_PERIOD = 'send_period'
LAST_SEND = 'last_send'
SEND_TIME = 'send_time'


def config_read(file_name: str):
    config = configparser.ConfigParser()

    try:
        res = config.read(file_name, encoding='utf-8')
    except configparser.MissingSectionHeaderError as err:
        raise classes.ConfigError(err, f'В фале {file_name} отсутствует раздел [{SECTION}]')

    if not res:
        pass

    message_edit_conf = f'Пожалуйста отредактируйте файл конфигурации {file_name} согласно инструкции!'
    if config.has_section(SECTION):
        if not config.has_option(SECTION, HABR_BLOG):
            message = f'Параметр {HABR_BLOG} в разделе {SECTION} (адрес блога на habr.com) ' \
                      f'остутствует в файле конфигурации!'
            print(message)
            config.set(SECTION, HABR_BLOG, '')
            config_write(config, file_name)
            raise classes.ConfigError(message+'\n'+message_edit_conf)
        else:
            if not config[SECTION][HABR_BLOG]:
                message = f'Параметр {HABR_BLOG} в разделе {SECTION} (адрес блога на habr.com) ' \
                          f'не задан!'
                raise classes.ConfigError(message + '\n' + message_edit_conf)

        if not config.has_option(SECTION, POLL_PERIOD):
            config.set(SECTION, POLL_PERIOD, '5')
            message = f'Параметр {POLL_PERIOD} в разделе {SECTION} (период парсинга блога) не задан ' \
                      f'в файле конфигурации!\nУстановлено значение по умолчанию (в минутах) {POLL_PERIOD} = 5'
            print(message)
            config_write(config, file_name)

        if not config.has_option(SECTION, BOT_TOKEN):
            message = f'Параметр {BOT_TOKEN} в разделе {SECTION} (токен slack бота) ' \
                      f'не задан!'
            config.set(SECTION, BOT_TOKEN, '')
            config_write(config, file_name)
            raise classes.ConfigError(message+'\n'+message_edit_conf)
        else:
            if not config[SECTION][BOT_TOKEN]:
                message = f'Параметр {BOT_TOKEN} в разделе {SECTION} (токен slack бота) ' \
                          f'не задан!'
                raise classes.ConfigError(message + '\n' + message_edit_conf)

        if not config.has_option(SECTION, CHANNEL):
            message = f'Параметр {CHANNEL} в разделе {SECTION} (кнал в Slack) остутствует в файле конфигурации!'
            print(message)
            config.set(SECTION, CHANNEL, '')
            config_write(config, file_name)
            raise classes.ConfigError(message+'\n'+message_edit_conf)
        else:
            if not config[SECTION][CHANNEL]:
                message = f'Параметр {CHANNEL} в разделе {SECTION} (кнал в Slack) ' \
                          f'не задан!'
                raise classes.ConfigError(message + '\n' + message_edit_conf)

        if not config.has_option(SECTION, TEXT):
            config.set(SECTION, TEXT, '')
            config_write(config, file_name)
            message = f'Параметр {TEXT} в разделе {SECTION} (текст сообщения рассылки) не задан в файле конфигурации!'
            print(message)
        else:
            if not config[SECTION][TEXT]:
                message = f'Параметр {TEXT} в разделе {SECTION} (текст сообщения рассылки) не задан в ' \
                          f'файле конфигурации!'
                print(message)

        if not config.has_option(SECTION, TAGS):
            config.set(SECTION, TAGS, '')
            config_write(config, file_name)
            message = f'Параметра {TAGS} в разделе {SECTION} (тэги) нет в файле конфигурации!'
            print(message)

        if not config.has_option(SECTION, SEND_PERIOD):
            config.set(SECTION, SEND_PERIOD, '')
            message = f'Параметр {SEND_PERIOD} в разделе {SECTION} (рассылка новых статей) не задан в ' \
                      f'файле конфигурации!\nУстановлено значение по умолчанию (в сутках) {SEND_PERIOD} = '
            config_write(config, file_name)
            print(message)

        if not config.has_option(SECTION, SEND_TIME):
            config.set(SECTION, SEND_TIME, '')
            message = f'Параметр {SEND_TIME} в разделе {SECTION} (время рассылки) не задан в файле конфигурации!\n' \
                      f'Установлено значение по умолчанию (при обнаружении новой статьи) {SEND_TIME} = '
            config_write(config, file_name)
            print(message)

        if not config.has_option(SECTION, LAST_SEND):
            config.set(SECTION, LAST_SEND, '')
    else:
        config.add_section(SECTION)
        config.set(SECTION, HABR_BLOG, '')
        config.set(SECTION, POLL_PERIOD, '5')
        config.set(SECTION, BOT_TOKEN, '')
        config.set(SECTION, CHANNEL, '')
        config.set(SECTION, TEXT, '')
        config.set(SECTION, TAGS, '')
        config.set(SECTION, SEND_PERIOD, '')
        config.set(SECTION, SEND_TIME, '')
        config.set(SECTION, LAST_SEND, '')

        config_write(config, file_name)
        raise classes.ConfigError(message_edit_conf)

    return config


def config_write(config: configparser.ConfigParser, file_name: str):
    config_instruction = f'# Это файл конфигурации программы repulser.\n\n' \
                         f'# Файл должен содержать раздел [{SECTION}] \n\n' \
                         f'# Описание параметров раздела:\n' \
                         f'# {HABR_BLOG} = https://habr.com/ru/company/skillfactory/blog/\n' \
                         f'#Параметр {HABR_BLOG} задает ссылку на блог Skillfactory на habr.com.\n' \
                         f'#Параметр обязательно должен быть задан!\n\n' \
                         f'#{POLL_PERIOD} = 5\n' \
                         f'#Параметр {POLL_PERIOD} задает период проверки новых статей на блоге в минутах.\n' \
                         f'#Если задан параметр {SEND_PERIOD} - то параметр {POLL_PERIOD} не исползуется.\n\n' \
                         f'#{BOT_TOKEN} = <токен вашего Slack-бота>\n' \
                         f'#В параметр {BOT_TOKEN} указывается токен вашего Slak-бота.\n' \
                         f'#Параметр обязательно должен быть задан!\n\n' \
                         f'#{CHANNEL} = <имя канала>\n' \
                         f'#В параметре {CHANNEL} нужно указать канал в Slack куда будет осуществляться рассылка.\n' \
                         f'#Параметр обязательно должен быть задан!\n\n' \
                         f'#{TEXT} = <текст сообщения в Slack>\n' \
                         f'#В параметре {TEXT} задается текст сообщения, которое будет отправлено в Slack\n\n' \
                         f'#{TAGS} = <тэги для фильтрации постов, через запятую>\n' \
                         f'#В параметре {TAGS} задаются тэги для фильтрации постов, которые будут отправлены в ' \
                         f'Slack.\n' \
                         f'# Указываются через запятую. Для отправки всех постов оставьте параметр пустым\n\n' \
                         f'# {SEND_PERIOD} = 1\n' \
                         f'# В параметре {SEND_PERIOD} указывается период в днях для рассылки постов.\n' \
                         f'# Рассылка будет осуществлена во время, указанное в параметре {SEND_TIME}.\n' \
                         f'# Если необходимо рассылать посты сразу после появления в блоге - оставьте поле пустым,\n' \
                         f'# тогда наличие новых постов будет проверятся с периодом указанным в параметре ' \
                         f'{POLL_PERIOD}\n' \
                         f'# (в минутах) и сразу рассылаться\n\n' \
                         f'# {SEND_TIME} = 9:30\n' \
                         f'# В параметре {SEND_TIME} задается время рассылки новых постов в формате HH:MM\n\n' \
                         f'# {LAST_SEND} = 2021-04-03T19:02:28.176633\n' \
                         f'# В параметре {LAST_SEND} указана дата и время последней рассылки.\n' \
                         f'# Елси параметр будет не задан, программа осуществит рассылку в ближайшее время, ' \
                         f'указанное\n' \
                         f'# в параметре {SEND_TIME}, при этом будут высланы все посты опубликованные за ' \
                         f'количество \n' \
                         f'# дней, указанных в {SEND_PERIOD} до времени {SEND_TIME}.\n' \
                         f'# Если {SEND_TIME} не задан, то рассылка будет осуществлена в момент запуска программы.\n\n'

    with open(file_name, 'w', encoding='utf-8') as configfile:
        configfile.write(config_instruction)
        config.write(configfile)


if __name__ == '__main__':
    main()
