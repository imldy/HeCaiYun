# -*- coding: UTF-8 -*-
# Desc: 和彩云自动打卡签到 gen: SCF-GENERATE
# Time: 2020/02/20 12:53:28
# Auth: xuthus
# SIG: QQ Group(824187964)

import json
from urllib import parse
import time
import os, sys
import requests


def get_datetime():
    local_time = time.localtime()
    dt = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    return dt


def log(text):
    print("{} - {}".format(get_datetime(), text))


class Tools():
    @classmethod
    def cool_push(cls, push_key: str, title: str, content: str):
        url = "https://push.xuthus.cc/send/" + push_key
        data = title + "\n" + content
        # 发送请求
        res = requests.post(url=url, data=data.encode('utf-8')).text
        # 输出发送结果
        return res

    @classmethod
    def serverChanPush(cls, Sckey: str, text: str, desp: str):
        # Server酱通知服务
        serverChan_res = requests.get(
            'https://sc.ftqq.com/' + Sckey + '.send?text=' + text + '&desp=' + desp)
        return serverChan_res

    @classmethod
    def serverChanTurboPush(cls, SendKey: str, text: str, desp: str):
        # Server酱通知服务
        serverChan_res = requests.get(
            'https://sctapi.ftqq.com/' + SendKey + '.send?title=' + text + '&desp=' + desp)
        return serverChan_res

    @classmethod
    def WorkWeChatGroupBotPush(cls, push_key: str, title: str, content: str):
        if push_key.startswith("https://"):
            url = push_key
        else:
            url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}".format(key=push_key)
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": "### {title}\n\n{content}".format(title=title, content=content)
            }
        }
        res = requests.post(url=url, data=json.dumps(data))
        return res

    @classmethod
    def push(cls, push_key: str, title: str, content: str):
        '''
        通过push_key前缀判断使用的推送方式
        1、Cool Push（酷推）：前缀使用“coolpush://”，例如"coolpush://cfde4cd50e4e7386590000000000000"
        2、Server酱：前缀使用“sc://”
        3、Server酱Turbo版：前缀使用“sct://”
        4、企业微信群机器人：前缀使用“wwcg://”
        其他格式一律不推送
        :param push_key:
        :param title:
        :param content:
        :return:
        '''
        if "" == push_key or len(push_key) < len("://"):  # 代表未定义推送方式，为什么长度判断之前还要判断是不是空字符串
            log("未定义推送方式")
            return
        fields = push_key.split("://")
        channel = fields[0] + "://"
        key = push_key[len(channel):]
        if "coolpush://" == channel:
            cls.cool_push(key, title, content)
            log("酷推推送结束")
        elif "sc://" == channel:
            cls.serverChanPush(key, title, content)
            log("Server酱推送结束")
        elif "sct://" == channel:
            cls.serverChanTurboPush(key, title, content)
            log("Server酱Turbo推送结束")
        elif "wwcg://" == channel:
            cls.WorkWeChatGroupBotPush(key, title, content)
            log("企业微信群机器人推送结束")
        else:
            log("不推送")


class Account():
    def __init__(self, Cookie):
        self.OpenLuckDraw = False  # 是否开启自动幸运抽奖(首次免费, 第二次5积分/次) 不建议开启 否则会导致多次执行时消耗积分
        self.push_key = ""  # 推送的key，酷推、Server酱、微信群机器人等赋值于此
        self.Cookie = Cookie  # 抓包Cookie 存在引号时 请使用 \ 转义
        self.Referer = "https://caiyun.feixin.10086.cn:7071/portal/newsignin/index.jsp"  # 抓包referer
        self.UA = "Mozilla/5.0 (Linux; Android 10; M2007J3SC Build/QKQ1.191222.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.106 Mobile Safari/537.36 MCloudApp/7.6.0"
        self.session = requests.session()
        self.session.headers = {
            "Host": "caiyun.feixin.10086.cn:7070",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": self.UA,
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "http://caiyun.feixin.10086.cn:7070",
            "Referer": self.Referer,
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cookie": self.Cookie,
        }

    def getEncryptTime(self):
        target = "http://caiyun.feixin.10086.cn:7070/portal/ajax/tools/opRequest.action"
        payload = parse.urlencode({
            "op": "currentTimeMillis"
        })
        resp = json.loads(self.session.post(target, data=payload).text)
        if resp['code'] != 10000:
            log('获取时间戳失败: {}'.format(resp['msg']))
            return 0
        return resp['result']

    def getTicket(self):
        target = "https://proxy.xuthus.cc/api/10086_calc_sign"
        payload = {
            "sourceId": 1003,
            "type": 1,
            "encryptTime": self.getEncryptTime()
        }
        resp = json.loads(requests.post(target, data=payload).text)
        if resp['code'] != 200:
            log('加密失败: {}'.format(resp['msg']))
        return resp['data']

    def luckDraw(self):
        target = "http://caiyun.feixin.10086.cn:7070/portal/ajax/common/caiYunSignIn.action"
        payload = parse.urlencode({
            "op": "luckDraw",
            "data": self.getTicket()
        })
        resp = json.loads(self.session.post(target, data=payload).text)

        if resp['code'] != 10000:
            log('自动抽奖失败: {}'.format(resp['msg']))
            return '自动抽奖失败: ' + resp['msg']
        else:
            if resp['result']['type'] == '40160':
                return '自动抽奖成功: 小狗电器小型手持床铺除螨仪'
            elif resp['result']['type'] == '40175':
                return '自动抽奖成功: 飞科男士剃须刀'
            elif resp['result']['type'] == '40120':
                return '自动抽奖成功: 京东京造电动牙刷'
            elif resp['result']['type'] == '40140':
                return '自动抽奖成功: 10-100M随机长期存储空间'
            elif resp['result']['type'] == '40165':
                return '自动抽奖成功: 夏新蓝牙耳机'
            elif resp['result']['type'] == '40170':
                return '自动抽奖成功: 欧莱雅葡萄籽护肤套餐'
            else:
                return '自动抽奖成功: 谢谢参与'

    def sign_in(self):
        target = "http://caiyun.feixin.10086.cn:7070/portal/ajax/common/caiYunSignIn.action"

        ticket = self.getTicket()
        payload = parse.urlencode({
            "op": "receive",
            "data": ticket,
        })

        resp = json.loads(self.session.post(target, data=payload).text)
        if resp['code'] != 10000:
            Tools.push(self.push_key, '【失败】和彩云签到', '失败:' + resp['msg'])
        else:
            content = '签到成功\n本月累计签到:' + str(resp['result']['monthDays']) + '天\n总积分:' + str(resp['result']['totalPoints'])
            if self.OpenLuckDraw:
                log("开始抽奖")
                resp_luckDraw = self.luckDraw()
                content += '\n' + resp_luckDraw
            log(content)
            Tools.push(self.push_key, '【成功】和彩云签到', content)


def run(Cookie: str, OpenLuckDraw: bool, push_key: str):
    account = Account(Cookie)
    account.OpenLuckDraw = OpenLuckDraw
    account.push_key = push_key
    account.sign_in()


def conf_file_run(account_conf_file):
    with open(account_conf_file) as f:
        account_conf = json.loads(f.read())
    for account in account_conf:
        log("开始账号")
        run(account["Cookie"], account["OpenLuckDraw"], account["push_key"])


def cli_arg_run(argv):
    '''
    命令行参数启动
    :return:
    '''
    Cookie_list = argv[1].split("#")
    OpenLuckDraw_list = argv[2].split("#")
    # todo: 处理参数不足的问题
    push_key_list = argv[3].split("#")
    if len(Cookie_list) != len(OpenLuckDraw_list):
        log("请确保<Cookie>和<是否开启抽奖的设置>数量一致")
    for i in range(0, len(Cookie_list)):
        Cookie = Cookie_list[i]
        OpenLuckDraw = False  # 默认不开启抽奖
        try:
            if "ture" == OpenLuckDraw_list[i]:  # 如果设置了ture才开启
                OpenLuckDraw = True
        except IndexError as e:
            log("OpenLuckDraw配置数量不足，采用默认")
        # elif "false" == OpenLuckDraw_list[i]:
        #     OpenLuckDraw = False

        # 如果push_key的数量没有cookie的多，则只使用第一个push_key，否则按顺序使用
        if len(push_key_list) < len(Cookie_list):
            push_key = push_key_list[0]
        else:
            push_key = push_key_list[i]
        log("开始账号")
        run(Cookie, OpenLuckDraw, push_key)


def tencent_SCF_run(event, context):
    environment = eval(context["environment"])
    if environment.has_key('push_key'):
        push_key = environment["push_key"]
    else:
        push_key = ""
    cli_arg_run([environment["SCF_NAMESPACE"], environment["Cookie"], environment["OpenLuckDraw"], push_key])


# 本地测试
if __name__ == '__main__':
    if len(sys.argv) > 1:
        log("命令行参数启动")
        log("因cookie过于长，暂不支持命令行输入cookie等参数")
        exit(1)
        cli_arg_run(sys.argv)
    else:
        log("账号配置文件启动")
        if os.path.exists("account_conf_dev.json"):
            log("读取开发模式的用户配置文件并启动")
            account_conf_file = "account_conf_dev.json"
        else:
            account_conf_file = "account_conf.json"
        if not os.path.exists(account_conf_file) or not os.path.isfile(account_conf_file):
            log("不存在账号配置文件{}".format(account_conf_file))
            exit(1)
        else:
            conf_file_run(account_conf_file)
