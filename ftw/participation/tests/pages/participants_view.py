from ftw.testbrowser import browser
from operator import itemgetter


def table():
    return browser.css('#content table.listing').first.dicts()


def users_column():
    return map(itemgetter('User'), table())
