# Cloud Analysis

## 简要介绍

- 角色：IoT 云边端架构——云端分析应用
- 功能：异常数据检测
- 参考：[蔡金川,张超,樊丽. 基于ZigBee和GPRS的智能家居设计以及传感数据基于时间序列的聚类分析[J]. 新型工业化,2017,7(3):25-32. DOI:10.19335/j.cnki.2095-6649.2017.03.005.](https://d.wanfangdata.com.cn/periodical/xxgyh201703005)

## 工作流程

- 云服务器每天定时执行此应用
- 首先，执行 [query_tool.py](./query_tool.py)
    - 通过云平台接口查询设备全部历史数据
    - 集成、转换数据，持久化为 `.csv` 文件
- 其次，执行 [abnormal_detect.py](./abnormal_detect.py)
    - 从 `.csv` 文件中读取数据
    - 数据预处理
    - 构建时序模型
    - 构建聚类模型
    - 应用聚类模型，判断是否存在异常
    - 输出异常检测报告
- 工作人员查看异常检测报告，做出反馈

## 额外说明

- 目录下的 `.py` 文件为真正用于执行的脚本，`./research` 目录下为研究分析方法具体细节的 Jupyter Notebook 和数据, `./report` 目录下为生成的异常检测报告
- 分析方法整体思路按照参考文献制定，但在实现细节上略有不同
- 项目的主要目的是为了体现 IoT 云边端架构与分析应用的结合，因此只针对原始数据集中，设备 `00:0f:00:70:91:0a` 采集的 `temp` 温度数据进行分析，便于整体架构的调试和演示
