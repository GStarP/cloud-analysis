'''
从云平台下载设备最新数据, 转换为分析应用所需的格式, 持久化存储在文件中
'''
import requests
import json
import time

# 云平台 IP
url = "http://172.19.241.103:8080"


def getJWTToken(username, password):
    # 账号密码 JSON 化
    jsonStr = json.dumps({'username': username, 'password': password})
    # 请求认证接口
    res = requests.post(url + '/api/auth/login', jsonStr,
                        headers={
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        })
    # 返回响应中的 Token
    return 'Bearer ' + res.json()['token']


def curUnixTimestamp():
    return int(round(time.time() * 1000))


def queryDeviceData(token):
    device_id = '3acccbf0-ae8b-11ec-9b68-311e1b039506'
    # 请求历史数据接口
    res = requests.get(
        url + '/api/plugins/telemetry/DEVICE/' + device_id + '/values/timeseries',
        params={
            'keys': ['temp'],
            'startTs': 0,
            'endTs': curUnixTimestamp()
        },
        headers={
            'Content-Type': 'application/json',
            'X-Authorization': token
        })
    print(res.json())


# 云平台账户
username = "root1@thingsboard.org"
password = "123123"

# 登录, 获取 JWT Token
token = getJWTToken(username, password)

# 查看指定设备数据
queryDeviceData(token)
