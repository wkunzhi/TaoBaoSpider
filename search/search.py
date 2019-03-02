# -*- coding: utf-8 -*-
# __author__ = "zok" 
# Date: 2019/3/1  Python: 3.7
import re
import pymysql

from search.getIP import option
from selenium import webdriver
from config import SERVICE_ARGS
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq


class Search(object):
    """
    搜索类
    """
    chrome_options = webdriver.ChromeOptions()

    # 禁止图片策略
    # prefs = {"profile.managed_default_content_settings.images": 2}
    # chrome_options.add_experimental_option("prefs", prefs)

    # 拦截端口
    chrome_options.add_argument("--proxy-server=http://127.0.0.1:8080")
    browser = webdriver.Chrome(executable_path='./utils/chromedriver', chrome_options=chrome_options)

    # 无头
    # browser = webdriver.PhantomJS(executable_path='./utils/phantomjs')

    wait = WebDriverWait(browser, 10, 0.1)

    def __init__(self, key):
        self.key = key

    def start(self):
        try:
            total = self.search()
            total = int(re.compile('(\d+)').search(total).group(1))
            for i in range(2, total + 1):
                self.next_page(i)
        except Exception:
            print('出错啦')
            self.browser.close()
        finally:
            self.browser.close()

    def search(self):
        print('正在搜索')
        try:
            # 正式入口
            self.browser.get('https://www.taobao.com')

            # 测试网址
            # self.browser.get('https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html')

            input_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
            )
            submit = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button')))
            input_box.send_keys(self.key)
            submit.click()
            total = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total')))
            self.get_products()
            return total.text
        except TimeoutException:
            return self.search()

    def next_page(self, page_number):
        print('正在翻页', page_number)
        try:
            input_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
            )
            submit = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
            input_box.clear()
            input_box.send_keys(page_number)
            submit.click()
            self.wait.until(EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number)))
            self.get_products()
        except TimeoutException:
            self.next_page(page_number)

    def get_products(self):
        """解析数据"""
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
        html = self.browser.page_source
        doc = pq(html)
        items = doc('#mainsrp-itemlist .items .item').items()
        for item in items:
            product = {
                'image': item.find('.pic .img').attr('src'),  # 宝贝图片
                'price': item.find('.price').text()[2:],  # 宝贝价格
                'goods_url': item.find('.J_ClickStat').attr('href'),  # 宝贝链接
                'pay_num': item.find('.deal-cnt').text()[:-3],  # 交易人数
                'title': item.find('.title').text().replace('\n', ''),  # 宝贝标题
                'shop': item.find('.shop').text(),  # 店铺ID
                'shop_url': item.find('.J_ShopInfo').attr('href'),  # 店铺url
                'location': item.find('.location').text()  # 店铺地址
            }
            self.save_to_mysql(product)

    def save_to_mysql(self, product):
        """
        插入到数据库mysql
        :param product:
        :return:
        """
        image = product.get('image')
        price = product.get('price')
        goods_url = product.get('goods_url')
        pay_num = product.get('pay_num')
        title = product.get('title')
        shop = product.get('shop')
        shop_url = product.get('shop_url')
        location = product.get('location')

        # 数据库操作  【这里偷懒了，可以把这一段放在外面，不然每次插入都要链接数据库影响效率】
        db = pymysql.connect(host="localhost", user="root",
                             password="", db="taobao", port=3306)
        # 使用cursor()方法获取操作游标
        cur = db.cursor()
        sql_insert = """insert into bg_temp_spider(select_key,image,price,goods_url,pay_num,title,shop,shop_url,location) values("%s","%s","%s","%s","%s","%s","%s","%s","%s")""" % (
            self.key, image, price, goods_url, pay_num, title, shop, shop_url, location)
        try:
            cur.execute(sql_insert)
            db.commit()
        except Exception as e:
            print('错误回滚')
            db.rollback()
        finally:
            db.close()
