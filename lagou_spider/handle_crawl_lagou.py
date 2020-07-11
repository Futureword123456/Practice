import json
import re
import time
import multiprocessing
import requests
from lagou_spider.handle_insert_data import lagou_mysql
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
#定义一个类
class HandleLaGou(object):
    def __init__(self):
        #使用session保存cookie信息
        self.lagou_session = requests.session()
        #请求头
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
        }
        self.city_list = ""
        #获取全国所有城市列表的方法

    def handle_city(self):
        #通过正则表达式获取
        city_search = re.compile(r'www\.lagou\.com\/.*\/">(.*?)</a>')
        city_url = "https://www.lagou.com/jobs/allCity.html"
        city_result = self.handle_request(method="GET", url=city_url)
        #print(city_result)
        #使用正则表达式获取城市列表
        self.city_list = city_search.findall(city_result)
        #清除cookie信息
        self.lagou_session.cookies.clear()

    def handle_city_job(self,city):
        #first_request_url = "https://www.lagou.com/jobs/list_python?city=%s&cl=false&fromSearch=true&labelWords=&suginput="%city
        #first_request_url = "https://www.lagou.com/jobs/list_java?city=%s&cl=false&fromSearch=true&labelWords=&suginput="%city
        #first_request_url = "https://www.lagou.com/jobs/list_大数据?city=%s&cl=false&fromSearch=true&labelWords=&suginput="%city
        first_request_url = "https://www.lagou.com/jobs/list_大数据?city=%s&cl=false&fromSearch=true&labelWords=&suginput="%city

        first_response = self.handle_request(method="GET", url=first_request_url)
        total_page_search = re.compile(r'class="span\stotalNum">(\d+)</span>')
        try:
            total_page = total_page_search.search(first_response).group(1)
        #如果没有岗位信息直接except
        except:
            return
        else:
            for i in range(1, int(total_page) + 1):
                data = {
                    "pn": i,
                    #"kd": "python"
                    "kd": "大数据"
                }
                page_url = "https://www.lagou.com/jobs/positionAjax.json?city=%s&needAddtionalResult=false" % city
                #python
                #referer_url = "https://www.lagou.com/jobs/list_python?city=%s&cl=false&fromSearch=true&labelWords=&suginput=" % city
                #java
                #referer_url = "https://www.lagou.com/jobs/list_java?city=%s&cl=false&fromSearch=true&labelWords=&suginput="% city

                #referer_url = "https://www.lagou.com/jobs/list_大数据?city=%s&cl=false&fromSearch=true&labelWords=&suginput="% city
                referer_url = "https://www.lagou.com/jobs/list_大数据?city=%s&cl=false&fromSearch=true&labelWords=&suginput="% city

                # referer的URL需要进行encode
                self.header['Referer'] = referer_url.encode()
                response = self.handle_request(method="POST", url=page_url, data=data, info=city)
                lagou_data = json.loads(response)
                job_list = lagou_data['content']['positionResult']['result']
                for job in job_list:
                    lagou_mysql.insert_item(job)

    def handle_request(self, method, url, data=None, info=None):
        while True:
            # # 加入阿布云的动态代理
            # proxyinfo = "http://%s:%s@%s:%s" % ('D0124B3C8AE62C12', '1474F0DC353A', 'http-dyn.qg.net', '48039')
            # proxy = {
            #     "http": proxyinfo,
            #     "https": proxyinfo
            # }
            try:
                if method == "GET":
                    response = self.lagou_session.get(url=url, headers=self.header, verify=False, timeout=6)
                elif method == "POST":
                    response = self.lagou_session.post(url=url, headers=self.header, data=data, verify=False, timeout=6)
            except:
                # 需要先清楚cookie信息
                self.lagou_session.cookies.clear()
                # 重新获取cookies信息
                #python
                #first_request_url = "https://www.lagou.com/jobs/list_python?city=%s&cl=false&fromSearch=true&labelWords=&suginput=" % info
                #first_request_url = "https://www.lagou.com/jobs/list_java?city=%s&cl=false&fromSearch=true&labelWords=&suginput=" % info
                #first_request_url = "https://www.lagou.com/jobs/list_大数据?city=%s&cl=false&fromSearch=true&labelWords=&suginput=" % info
                first_request_url = "https://www.lagou.com/jobs/list_大数据?city=%s&cl=false&fromSearch=true&labelWords=&suginput=" % info

                self.handle_request(method="GET", url=first_request_url)
                # 休眠10秒
                time.sleep(10)
                continue
            response.encoding = 'UTF-8'
            #防止多次访问被停止
            if '频繁' in response.text:
                print(response.text)
                #需要先清楚cookie信息
                self.lagou_session.cookies.clear()
                #重新获取cookies信息
                #first_request_url = "https://www.lagou.com/jobs/list_python?city=%s&cl=false&fromSearch=true&labelWords=&suginput=" % info
                #first_request_url = "https://www.lagou.com/jobs/list_java?city=%s&cl=false&fromSearch=true&labelWords=&suginput=" % info
                #first_request_url = "https://www.lagou.com/jobs/list_大数据?city=%s&cl=false&fromSearch=true&labelWords=&suginput=" % info
                first_request_url = "https://www.lagou.com/jobs/list_大数据?city=%s&cl=false&fromSearch=true&labelWords=&suginput=" % info

                self.handle_request(method="GET", url=first_request_url)
                #休眠10秒
                time.sleep(10)
                continue
            return response.text

if __name__ == '__main__':
    lagou = HandleLaGou()
    #获取所有城市方法
    lagou.handle_city()
    #引入多进程
    pool = multiprocessing.Pool(5)
    for city in lagou.city_list:
        pool.apply_async(lagou.handle_city_job, args=(city,))
    pool.close()
    pool.join()
