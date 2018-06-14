import requests
import time
import re
import os
import station
from prettytable import PrettyTable

class Ticket:
    def __init__(self, station):
        #搜索条件列表
        self.config = []
        self.search_url = ''
        #查询间隔
        self.sleep_sec = 10
        self.station = station
        #创建会话对象
        self.s = requests.Session()
        #超时时间
        self.s.timeout = 5

        #设置表头
        self.table = PrettyTable([
            '状态',
            '车次',
            '出发站',
            '到达站',
            '出发时间',
            '到达时间',
            '历时',
            '有票',
            '无座',
            '硬座',
            '硬卧',
            '软卧',
            '一等座',
            '二等座',
            '商务座',
        ])
    def main(self):
        count = 0
        while True:
            count += 1
            print('第{}次查询,{}秒后再次查询'.format(count, self.sleep_sec))
            self.main_loop()
            print()
            #延时重启
            time.sleep(self.sleep_sec)

    def addsearch(self, form, preg_filter, time_filter):
        self.config.append({
            #查询参数配置
            'form':form,
            #过滤
            'filter':preg_filter,
            #时间过滤
            'time_filter':time_filter
        })

    def generate_url(self, form):
        if self.search_url == '':
            self.search_url = "https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={}&leftTicketDTO.from_station={}&leftTicketDTO.to_station={}&purpose_codes={}".format(
                form['train_date'],
                station.name2id(form['from_station']),
                station.name2id(form['to_station']),
                form['purpose_codes']
            )
        #print(url)
        return self.search_url
    def main_loop(self):
        #遍历所有配置项
        for config_item in self.config:
            self.table.clear_rows()

            response = self.s.get(self.generate_url(config_item['form']))

            if response.status_code != 200:
                print('网络错误,status_code:{}'.format(response.status_code))
                continue
            if response.text.find('{"data":{"flag"') != 0:
                print('页面错误.')
                continue
            try:
                response = response.json().get('data').get('result')
            except:
                with open('./json.log','w') as file:
                    file.write(response.text)
                exit()
            for item in self.format_train(response):
                if self.filter_train(config_item, item):
                    self.table.add_row([
                        item['state'],
                        item['train_id'],
                        item['search_start'],
                        item['search_stop'],
                        item['time_in'],
                        item['time_out'],
                        item['time_travel'],
                        '有票' if item['have_ticket']=='Y' else '没票',
                        item['无座'],
                        item['硬座'],
                        item['硬卧'],
                        item['软卧'],
                        item['一等座'],
                        item['二等座'],
                        item['商务座'],
                    ])
                    
                    if self.train_buy_check(config_item, item):
                        print(self.table)
                        exit()
            self.table.reversesort = False
            self.table.sortby = '出发时间'
            print(self.table)
    #买票过滤
    def train_buy_check(self, config, item):
        #如果可购买，打开浏览器提醒买票
        if item['have_ticket'] != 'Y':
            return
        flag = False
        for col_name in config['filter']:
            if isinstance(config['filter'][col_name],int) and config['filter'][col_name]==1:
                if item[col_name] != '无' and item[col_name] != '--' and item[col_name] != '':
                    note = '{}/{}/{}/{}'.format(
                            config['form']['train_date'],
                            item['search_start'],
                            item['search_stop'],
                            item['train_id']
                        )
                    print(note)
                    os.system('chrome https://kyfw.12306.cn/otn/leftTicket/init?notice=' + note)
                    return True
        return False
    #展示过滤
    def filter_train(self, config, item):
        #遍历正则过滤
        for col_name in config['filter']:
            if isinstance(config['filter'][col_name],list) and config['filter'][col_name] != []:
                #任何一项匹配
                flag = False
                for preg in config['filter'][col_name]:
                    if re.match(preg, item[col_name]):
                        flag = True
                        break
                if not flag:
                    return False

        #发车时间过滤
        for time_item in config['time_filter']:
            if config['time_filter'][time_item]:
                tmp = time_item.split('-')
                if item['time_in'] < tmp[0] or item['time_in'] > tmp[1]:
                    return False
        return True

    def format_train(self, train_list):
        for train in train_list:
            info = train.split('|')
            yield {
                'xcode1':info[0],
                'state':info[1], # 状态 预定
                'train_no':info[2],
                'train_id':info[3], # 车次 T3037
                'train_start':self.station.id2name(info[4]), # 始发站
                'train_stop':self.station.id2name(info[5]), # 终点站
                'search_start':self.station.id2name(info[6]), # 购买起点站
                'search_stop':self.station.id2name(info[7]), # 购买到达站
                'time_in':info[8], # 出发时间
                'time_out':info[9], # 到达时间
                'time_travel':info[10], # 历经时间
                'have_ticket':info[11], # 是否可购买 Y
                'xcode3':info[12], # 
                'train_begin_date':info[13], # 车次发车日期
                'xcode4':info[14], # 
                'xcode5':info[15], # 
                'train_sort_begin':info[16], # 站序排列起始
                'train_sort_end':info[17], # 站序排列结束
                'xcode6':info[18], # 
                'xcode7':info[19], # 
                'xcode8':info[20], # 
                'xcode9':info[21], # 
                'xcode10':info[22], # 
                '软卧':info[23], # 软卧数量
                'xcode11':info[24], # 
                'xcode12':info[25], # 
                '无座':info[26], # 无座数量
                'xcode13':info[27], # 
                '硬卧':info[28], # 硬卧数量
                '硬座':info[29], # 硬座数量
                '二等座':info[30], # 二等座
                '一等座':info[31], # 一等座
                '商务座':info[32], # 商务座
                'xcode14':info[33], # 
                'xcode15':info[34], # 
                'xcode16':info[35], # 
                'exchange':info[36] # 可兑换 [1,0]
            }

if __name__ == '__main__':
    station = station.Station()
    ticket = Ticket(station)
    #回家车票
    #
    ticket.addsearch({
        'train_date':'2018-06-15',
        'from_station':'北京西',
        'to_station':'邢台',
        'purpose_codes':'ADULT'
    },{
        #'state':[],
        #'train_id':[],
        #'have_ticket':['Y','N'],
        '无座':0,
        '硬座':0,
        '硬卧':0,
        '软卧':0,
        '一等座':0,
        '二等座':0,
        '商务座':0,
    },{
        '00:00-23:59':0,
        '00:00-06:00':0,
        '06:00-12:00':0,
        '12:00-18:00':0,
        '18:00-23:59':1,
    })
    #回北京车票
    # ticket.addsearch({
        # 'train_date':'2018-02-21',
        # 'from_station':'西安',
        # 'to_station':'北京',
        # 'purpose_codes':'ADULT'
    # },{
        # 'search_start':[],
        # 'state':[],
        # 'train_id':['^(G|K).*'],
        # 'time_in':[],
        # 'time_out':['[^0]{2}:\d\d'],
        # 'have_ticket':['Y','N'],
        # 'wuzuo':[],
        # 'yingzuo':[],
        # '2dengzuo':[],
    # },{
        # 'time_in_min':'09:55',
        # 'time_in_max':'19:19',
        # 'time_out_max':'21:00'
    # })
    ticket.main()