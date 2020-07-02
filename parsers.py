from parsing_base import Parser
from typing import NamedTuple
from bs4 import BeautifulSoup
import re
import telebot
import config
import time


bot = telebot.TeleBot(config.TOKEN)


class KworkParser(Parser):
    KEYWORDS = ['парсинг', 'парсер', 'сбор', 'спарсить',
                'собрать', 'парсить', 'parser', 'parsing',
                'scraping']

    def __init__(self):
        super().__init__()
        self.host = 'https://kwork.ru/'
        self.projects_page = 'https://kwork.ru/projects?c=11'
        self.projects = []

    def get_response(self):
        resp = self.request.get(self.projects_page)
        return resp.text

    def update_projects(self):
        resp = self.get_response()
        soup = BeautifulSoup(resp, 'lxml')
        projects_blocks = soup.select('.mb15')
        for project_block in projects_blocks:
            url = project_block.select_one('.wants-card__header-title.first-letter.breakwords').select_one('a')['href']
            header = project_block.select_one('.wants-card__header-title.first-letter.breakwords').text
            price = project_block.select_one('.wants-card__header-price.wants-card__price.m-hidden').text
            description = project_block.select_one('.breakwords.first-letter.f14.lh22').text
            price = float(''.join(re.findall('\d', price)))
            project = Project(freelance_site=self.host, header=header, description=description, price=price, url=url)
            if project in self.projects:
                continue
            if self.is_suitable_project(project):
                self.projects.append(project)
                project.telegram_info()

    def is_suitable_project(self, project):
        for key in self.KEYWORDS:
            if re.findall(key, project.header.lower()):
                return True
            if re.findall(key, project.description.lower()):
                return True


class Project(NamedTuple):
    freelance_site: str
    header: str
    description: str
    url: str
    price: float

    def telegram_info(self):
        message = f"\t<b>Фриланс биржа</b>: {self.freelance_site}\n" \
                  f"\t<b>Задание:/b> {self.header}\n" \
                  f"\t<b>Подробности:/b> {self.description}\n" \
                  f"\t<b>Цена:/b> {self.price}\n" \
                  f"\t<b>Ссылка:/b> {self.url}\n"
        bot.send_message(config.CHAT_ID, message, parse_mode='html')


def main():
    parser = KworkParser()
    while True:
        parser.update_projects()
        time.sleep(300)


if __name__ == '__main__':
    main()