import pandas as pd
import numpy as np
from statsmodels.tsa import stattools
from statsmodels.tsa import arima_model
from sklearn.cluster import KMeans
import time

'''
读取数据
'''
# 完整数据的分析报告
# filename = './example.csv'
# 已上传数据量的分析报告
filename = './temp_humidity_sensor_1.csv'
df = pd.read_csv(filename)

'''
数据预处理
'''
# ts 转为 13 位 Unix Timestamp
df['ts'] = df.apply(lambda x: x*1000, axis=0)
# 以 ts 作为索引
df = df.set_index('ts')

# 以 temp 为例进行后续处理
ATTR = 'temp'
attr_ts = df[ATTR]

'''
构建时序模型
'''
# ARMA 模型中, 参数 ar 与 ma 的取值一般都为 0~4
max_ar = 4
max_ma = 4
# 遍历所有组合, 计算 AIC 等各项指标
select_res = stattools.arma_order_select_ic(attr_ts, max_ar, max_ma)
# 选取评价结果最好的参数
params = select_res.bic_min_order
# 拟合模型
ts_model = arima_model.ARMA(attr_ts, order=params).fit()
# 使用模型进行预测
attr_ts_predict = ts_model.predict()

'''
构建聚类模型
'''
# 以实际值与预测值的偏差作为聚类依据
attr_ts_bias = attr_ts - attr_ts_predict
# 转换数据格式以适应聚类需要
attr_ts_bias_reshaped = np.array(attr_ts_bias).reshape(-1, 1)
# 使用 KMeans 将数据分为三类: 可信/不确定/不可信
K = 3
cluster_model = KMeans(n_clusters=K)
# 拟合模型
cluster_model.fit(attr_ts_bias_reshaped)
# 保存分类结果
labels = cluster_model.labels_

'''
应用聚类模型
'''
# 将 实际值、预测值、分类 集成到一起
attr_ts_df = pd.DataFrame(
    columns=[ATTR], data=attr_ts.values, index=attr_ts.index)
attr_ts_df['predict'] = attr_ts_predict.values
attr_ts_df['label'] = labels

# 按类别分离
df_label = []
for i in range(K):
    df_label.append(attr_ts_df[attr_ts_df['label'] == i])

# 计算每种类别的均值偏差
for i in range(K):
    df = df_label[i]
    avg = abs(df_label[i][ATTR].mean() - df_label[i]['predict'].mean())
    df_label[i] = [df, avg]

# 按照均值偏差升序排列
df_label.sort(key=lambda x: x[1])

'''
判断是否存在异常
'''
# 理想情况下认为偏差最小为"可信", 其次为"不确定", 最大为"不可信"
reliable_df = pd.DataFrame(columns=['label'])
neural_df = pd.DataFrame(columns=['label'])
unreliable_df = pd.DataFrame(columns=['label'])
# 但也需要阈值进行控制, 否则全部可信的数据也会被强行分为三类
NEURAL_THREHOLD = 0.01 * attr_ts_df[ATTR].mean()
UNRELIABLE_THRESHOLD = 0.15 * attr_ts_df[ATTR].mean()

# 可信
reliable_df = df_label[0][0]

# 不确定
# 考虑到时序模型本身的偏差, 与阈值进行比较前要减去"可信"分类的均值偏差
neural_bias = df_label[1][1] - df_label[0][1]

if neural_bias < NEURAL_THREHOLD:
    reliable_df = pd.concat([reliable_df, df_label[1][0]])
elif neural_bias >= NEURAL_THREHOLD and neural_bias < UNRELIABLE_THRESHOLD:
    neural_df = df_label[1][0]
else:
    unreliable_df = df_label[1][0]

# 不可信
unreliable_bias = df_label[2][1] - df_label[0][1]

if unreliable_bias < NEURAL_THREHOLD:
    reliable_df = pd.concat([reliable_df, df_label[1][0]])
elif unreliable_bias >= NEURAL_THREHOLD and unreliable_bias < UNRELIABLE_THRESHOLD:
    if neural_df.empty:
        neural_df = df_label[2][0]
    else:
        neural_df = pd.concat([neural_bias, df_label[2][0]])
else:
    if unreliable_df.empty:
        unreliable_df = df_label[2][0]
    else:
        unreliable_df = pd.concat([unreliable_df, df_label[2][0]])

'''
输出异常报告
'''
# 总体情况
content = '【总体情况】\n'
# 总数据量: 1024, 处理数量: 1000
content = content + '总数据量: ' + str(attr_ts.count()) + ', 处理数量: ' + \
    str(attr_ts_df[ATTR].count()) + '\n'
# 均值: 20, 最小值: 0, 最大值: 20
# 1/4值: 16, 1/2值: 17, 3/4值: 17
content = content + '均值: ' + str(attr_ts_df[ATTR].mean()) + \
    ', 最小值: ' + str(attr_ts_df[ATTR].min()) + \
    ', 最大值: ' + str(attr_ts_df[ATTR].max()) + '\n' + \
    '1/4值: ' + str(attr_ts_df[ATTR].quantile(0.25)) + \
    ', 1/2值: ' + str(attr_ts_df[ATTR].quantile(0.5)) + \
    ', 3/4值: ' + str(attr_ts_df[ATTR].quantile(0.75)) + '\n'
# 可信数据: 900, 不确定数据: 80, 不可信数据: 20
content = content + '可信: ' + str(reliable_df['label'].count()) + \
    ', 不确定: ' + str(neural_df['label'].count()) + \
    ', 不可信: ' + str(unreliable_df['label'].count()) + '\n'
content = content + '\n'

# 不可信部分
if (unreliable_df.size > 0):
    content = content + '【不可信数据】\n'
    content = content + '相对均值偏差:\n'
    content = content + str(unreliable_bias) + '\n'
    content = content + '示例数据:\n'
    for i in range(3):
        if (i < unreliable_df.size):
            content += 'ts=' + str(unreliable_df.index[0]) +\
                ', real=' + str(unreliable_df.iloc[0][ATTR]) +\
                ', predict=' + str(unreliable_df.iloc[0]['predict']) + '\n'
    content = content + '全部数据:\n'
    content = content + ','.join(map(str, list(unreliable_df.index))) + '\n'
    content = content + '\n'

# 不确定部分
if (neural_df.size > 0):
    content = content + '【不确定数据】\n'
    content = content + '相对均值偏差:\n'
    content = content + str(neural_bias) + '\n'
    content = content + '示例数据:\n'
    for i in range(3):
        if (i < neural_df.size):
            content += 'ts=' + str(neural_df.index[0]) +\
                ', real=' + str(neural_df.iloc[0][ATTR]) +\
                ', predict=' + str(neural_df.iloc[0]['predict']) + '\n'
    content = content + '全部数据:\n'
    content = content + ','.join(map(str, list(neural_df.index))) + '\n'
    content = content + '\n'

# 可信部分
content = content + '【可信数据】\n'
content = content + '均值偏差:\n'
content = content + str(df_label[0][1])


# 输出文件
filename = time.strftime('%Y-%m-%d', time.localtime())
filepath = './report/' + filename + '.txt'
with open(filepath, 'w', encoding='UTF-8') as f:
    f.write(content)
    f.close()

'''
分析应用执行完毕
'''
print('analysis task finished, please check ' +
      filepath + ' for further information')
print(reliable_df['label'].count(),
      neural_df['label'].count(), unreliable_df['label'].count())
