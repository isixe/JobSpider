# JobSpider
 **[English](https://github.com/isixe/JobSpider/blob/main/README.md) | 中文**

Python 基于 Selenium 爬取招聘岗位信息的基础程序，支持 CSV 和 SQLite 数据存储

## 计划
- [x] 前程无忧
- [ ] Boss直聘

> [!TIP]
> 由于前程无忧接口限制，每个搜索词获取最大页数被限制为200

## 环境要求

```
Python 3.11.2
Edge
beautifulsoup4==4.12.2
colorlog==6.8.0
fake-useragent==1.4.0
pandas==2.1.3
selenium==4.15.2
requests==2.31.0
```

## 运行

```
pip install requirements.txt
```

运行示例 test/spider_test.py

## 项目结构

```
├─README.md 
├─LICENSE 
├─.gitignore 
├─requirements.txt 
├─log 
│ ├─handler_logger.py 
│ └─__init__.py 
├─output 
│ ├─area 
│ │ ├─51area.csv 
│ │ └─51area.db  
│ └─job 
│   ├─51job.csv 
│   └─51job.db   
├─spider 
│ ├─jobspider51.py 
│ ├─__init__.py 
│ └─area 
│  ├─areaspider51.py
│  └─__init__.py 
└─test 
  └─spider_test.py 
```

## 声明
> [!WARNING]
> 该程序仅用于学习研究，请勿用于任何商业或非法目的，若违反规定请自行对此负责，本人对此概不承担任何责任。
