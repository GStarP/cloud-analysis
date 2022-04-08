'''
从云平台下载设备最新数据, 转换为分析应用所需的格式, 持久化存储在文件中
'''
import requests
import json
import time

# 云平台地址
url = "http://172.19.241.103:18080"


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


# 获取当前时间的 Unix Timestamp
def curUnixTimestamp():
    return int(round(time.time() * 1000))


def queryDeviceData(token, device_id, keys):
    # 请求历史数据接口
    curTs = curUnixTimestamp()
    res = requests.get(
        url + '/api/plugins/telemetry/DEVICE/' + device_id + '/values/timeseries',
        params={
            'keys': keys,
            'startTs': 0,
            'endTs': curTs,
            'limit': 100000
        },
        headers={
            'Content-Type': 'application/json',
            'X-Authorization': token
        })
    data = res.json()
    # print(data)

    # 持久化为 CSV 文件
    content = 'ts,temp,humidity\n'
    ts_list = data['ts']
    temp_list = data['temp']
    humidity_list = data['humidity']
    p = 0
    min_len = min(len(ts_list), len(temp_list), len(humidity_list))
    while p < min_len:
        content += str(float(ts_list[p]['value'])) + ',' + \
            str(temp_list[p]['value']) + ',' + \
            str(humidity_list[p]['value']) + '\n'
        p += 1
    saveFile = './temp_humidity_sensor_1' + '.csv'
    with open(saveFile, 'w') as f:
        f.write(content)

    print('Device Data Fetched')


# 云平台账户
username = "root1@thingsboard.org"
password = "123123"

# 登录, 获取 JWT Token
token = getJWTToken(username, password)

# 查看指定设备数据
# 环境一下温湿度传感器的设备 ID
temp_humidity_sensor_1_id = 'f6079300-b552-11ec-b1a5-dfb596ee76e2'
# 查询 时间戳, 温度, 湿度 三项
query_keys = ['ts', 'temp', 'humidity']
queryDeviceData(token, temp_humidity_sensor_1_id, query_keys)
