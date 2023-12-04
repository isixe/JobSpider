# JobSpider

Python 基于 Selenium 爬取招聘岗位信息的基础程序，支持 CSV 和 SQLite 数据存储

# 计划
- [x] 前程无忧
- [ ] Boss直聘
- [ ] ~~智联招聘~~

> [!TIP]
> 由于前程无忧接口限制，每个搜索词最终获取最大条数被限制为1000

# 环境要求

```
Python 3.11.2
Edge
beautifulsoup4==4.12.2
colorlog==6.8.0
fake-useragent==1.4.0
pandas==2.1.3
selenium==4.15.2
```

# 运行

```
pip install requirements.txt
```

运行示例 test/spider_test.py

# 项目结构

```
├─README.md 
├─LICENSE 
├─.gitignore 
├─requirements.txt 
├─log 
│ ├─handler_logger.py 
│ └─__init__.py 
├─output 
│ ├─51job.csv 
│ └─51job.db 
├─spider 
│ ├─jobspider51.py 
│ └─__init__.py 
└─test 
  └─spider_test.py 
```

# 声明
> [!WARNING]
> 该程序仅用于学习研究，请勿用于任何商业或非法目的，若违反规定请自行对此负责，本人对此概不承担任何责任。
