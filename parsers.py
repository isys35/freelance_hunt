from parsing_base import Parser
from typing import NamedTuple
from bs4 import BeautifulSoup
import re
import telebot
import config
import time
from requests.exceptions import ConnectionError


bot = telebot.TeleBot(config.TOKEN)


class KworkParser(Parser):
    KEYWORDS = ['парсинг', 'парсер', 'парсера', 'сбор', 'спарсить',
                'собрать', 'парсить', 'parser', 'parsing',
                'scraping']

    def __init__(self):
        super().__init__()
        self.host = 'https://kwork.ru/'
        self.projects_page = 'https://kwork.ru/projects?=&c=41'
        self.projects = []

    def get_response(self):
        resp = self.request.get(self.projects_page)
        return resp.text

    def parsing_projects(self, soup):
        projects = []
        projects_blocks = soup.select('.mb15')
        for project_block in projects_blocks:
            url = project_block.select_one('.wants-card__header-title.first-letter.breakwords').select_one('a')['href']
            header = project_block.select_one('.wants-card__header-title.first-letter.breakwords').text
            price = project_block.select_one('.wants-card__header-price.wants-card__price.m-hidden').text
            description = project_block.select_one('.breakwords.first-letter.f14.lh22')
            if description:
                description = description.text
            price = ''.join(re.findall('\d', price)) + ' руб'
            project = Project(freelance_site=self.host, header=header, description=str(description), price=price, url=url)
            projects.append(project)
        return projects

    def update_projects(self):
        resp = self.get_response()
        soup = BeautifulSoup(resp, 'lxml')
        projects = self.parsing_projects(soup)
        for project in projects:
            if project in self.projects:
                continue
            if self.is_suitable_project(project):
                self.projects.append(project)
                project.telegram_info()

    def is_suitable_project(self, project):
        for key in self.KEYWORDS:
            if re.findall(key, project.header.lower().replace('\r', ' ').replace('\n', ' ')):
                return True
            if re.findall(key, project.description.lower().replace('\r', ' ').replace('\n', ' ')):
                return True


class WeblancerParser(KworkParser):
    def __init__(self):
        super().__init__()
        self.host = 'https://www.weblancer.net/'
        self.projects_page = 'https://www.weblancer.net/jobs/veb-programmirovanie-31/'
        self.projects = []

    def parsing_projects(self, soup):
        projects = []
        projects_blocks = soup.select('.row.click_container-link.set_href')
        for project_block in projects_blocks:
            url = self.host[:-1] + project_block.select_one('a.text-bold.show_visited')['href']
            header = project_block.select_one('a.text-bold.show_visited').text
            price_block = project_block.select_one('.float-right.float-sm-none.title.amount.indent-xs-b0')
            price_span_block = price_block.select_one('span')
            if not price_span_block:
                price = 'None'
            else:
                price = price_span_block.text
            description = project_block.select_one('.col-sm-10').select_one('p.text_field').text
            project = Project(freelance_site=self.host, header=header, description=description, price=price, url=url)
            projects.append(project)
        return projects


class Project(NamedTuple):
    freelance_site: str
    header: str
    description: str
    url: str
    price: str

    def telegram_info(self):
        message = f"\t<b>Фриланс биржа</b>: {self.freelance_site}\n" \
                  f"\t<b>Задание:</b> {self.header}\n" \
                  f"\t<b>Подробности:</b> {self.description}\n" \
                  f"\t<b>Цена:</b> {self.price}\n" \
                  f"\t<b>Ссылка:</b> {self.url}\n"
        print(message)
        while True:
            try:
                bot.send_message(config.CHAT_ID, message, parse_mode='html')
                break
            except ConnectionError:
                print('ConnectionError')
                time.sleep(10)


def main():
    parsers = [KworkParser(), WeblancerParser()]
    while True:
        print('Поиск проектов...')
        for parser in parsers:
            parser.update_projects()
        time.sleep(2)


if __name__ == '__main__':
    main()