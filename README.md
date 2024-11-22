# JobSpider
 **English | [中文](https://github.com/isixe/JobSpider/blob/main/README-cn.md)**

A Python basic program based on Selenium for crawling recruitment position information, supporting CSV and SQLite data storage

## Todo
- [x] 51job
- [ ] Boss zhipin

> [!TIP]
> Due to the limitation of 51job's API, the max page number of entries obtained per search term is limited to 200

## Environmental Requirement

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

## Usage

```
pip install requirements.txt
```

run test/spider_test.py

## Project Structure

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

## Statement
> [!WARNING]
> This program is only for learning and research purposes. Please do not use it for any business or illegal purpose. If you violate the regulations, please be responsible for yourself.。
