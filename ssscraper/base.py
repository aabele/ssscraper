# -*- coding:utf8 -*-
"""
Selenium wrapper for ss.lv website
"""
from __future__ import unicode_literals

import random
import string

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# Phantom JS config
phantomjs_config = dict(DesiredCapabilities.PHANTOMJS)
phantomjs_params = ['--ignore-ssl-errors=true', '--ssl-protocol=any', '--web-security=false']

PHANTOMJS_EXECUTABLE_PATH = 'phantomjs'


class Scraper(object):
    """
    SS.lv scraper
    """

    base_url = 'https://www.ss.lv'

    post_date_filter = {
        1: 'Šodien',
        2: 'Par 2 dienām',
        5: 'Par 5 dienām'
    }

    def __init__(self):
        self.driver = webdriver.PhantomJS(
            PHANTOMJS_EXECUTABLE_PATH,
            desired_capabilities=phantomjs_config,
            service_args=phantomjs_params)
        self.driver.set_window_size(1024, 768)

    @staticmethod
    def random(length):
        """ Generate random string """
        return ''.join(random.choice(string.ascii_letters) for i in range(length))

    def get_categories(self):
        """
        Get list of website top categories

        :return: [(title, url)], ...]
        :rtype: array
        """
        self.driver.get(self.base_url)
        items = self.driver.find_elements_by_xpath('//table//a[@class="a1"]')
        return [(i.text, i.get_attribute('href')) for i in items]

    def get_subcategories(self, category_url):
        """
        Get list of category sub categories

        :param category_url: top category url
        :type: string
        :return: [(title, url)], ...]
        :rtype: array
        """
        self.driver.get(category_url)
        items = self.driver.find_elements_by_xpath('//table//a[@class="a_category"]')
        return [(i.text, i.get_attribute('href')) for i in items]

    def get_posts(self, subcategory_url, days=None):
        """
        Get list of subcategory posts

        :param subcategory_url: top category url
        :type: string
        :param days: day filter - to filter posts by pub date
        :type: integer
        :return: [(title, url)], ...]
        :rtype: array
        """

        if days and days not in self.post_date_filter:
            raise Exception('Please set valid day filter')

        self.driver.get(subcategory_url)

        if days:
            days_xpath = "//select[@id='today_cnt_sl']/option[starts-with(text(), '%s')]" % self.post_date_filter.get(days)
            self.driver.find_element_by_xpath(days_xpath).click()

        data = []

        # Dealing with pagination
        # 1 vs True - because it's faster in python 2.*
        while 1:

            items = self.driver.find_elements_by_xpath('//table//a[@class="am"]')
            data += [(i.text, i.get_attribute('href')) for i in items]

            # Does not find next button at all - not enough items for pagination
            try:
                next_button = self.driver.find_element_by_xpath('//a[@class="navi" and @rel="next"]')
            except NoSuchElementException:
                break

            if not next_button.get_attribute('href').endswith('/'):
                next_button.click()
            else:
                # Next button links back to the first page
                break

        return data

    def get_post_details(self, post_url):
        """
        Get post details

        :param post_url: post url
        :type: string
        :return: post detail dictionary
        :rtype: dict
        """

        data = {}
        self.driver.get(post_url)

        delimiter = self.random(10)

        # Fixing bad quality html
        self.driver.execute_script(''.join((
            'var delimiter = document.createTextNode("' + delimiter + '");',
            'var table = document.getElementsByClassName("options_list")[0];',
            'table.parentNode.insertBefore(delimiter, table);',
        )))

        data['url'] = post_url
        body = self.driver.find_element_by_id('msg_div_msg').text
        data['body'] = body.split(delimiter)[0]

        # Properties
        keys = self.driver.find_elements_by_class_name('ads_opt_name')
        keys = [k.text.replace(':', '') for k in keys]
        values = self.driver.find_elements_by_class_name('ads_opt')
        values = [v.text for v in values]
        data['properties'] = dict(zip(keys, values))

        # Photos
        data['photos'] = []
        thumbs = self.driver.find_elements_by_class_name('pic_thumbnail')
        for thumb in thumbs:
            thumb.click()

            image = self.driver.find_element_by_id('msg_img')
            data['photos'].append(image.get_attribute('src'))

        # Fixing bad quality html
        self.driver.execute_script('document.querySelectorAll("[align=left]")[0].className = "ads_contacts";')

        # Contacts
        keys = [k.text for k in self.driver.find_elements_by_xpath('//td[@class="ads_contacts_name"]')]
        values = [v.text for v in self.driver.find_elements_by_xpath('//td[@class="ads_contacts"]')]
        data['contacts'] = list(zip(keys, values))

        return data


if __name__ == '__main__':
    scraper = Scraper()
    print(scraper.get_categories())
    print(scraper.get_subcategories('https://www.ss.lv/lv/transport/'))
    print(scraper.get_posts('https://www.ss.lv/lv/agriculture/agricultural-machinery/motoblocks/'))
    print(scraper.get_post_details('https://www.ss.lv/msg/lv/agriculture/agricultural-machinery/motoblocks/bbbkde.html'))
