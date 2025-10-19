# AI_Invest_Assistant
An AI investment assistant based on a large language model


### V1.1版本-2025年10月19日更新
#### 添加了日常在做基本面分析的时候可能会用到的一些数据指标
包括：
1. 公司概况get_company_profile()
2. 获取实时股票数据报价get_real_time_data()  PS:免费版有15-30分钟的延迟
3. 获取有关公司新闻get_company_news()  PS:免费版限制最近30天
4. 获取同行业其他公司列表get_company_peers()
5. 获取指定股票盈利日历(财报发布时间、实际业绩、市场预期数据以及对应季度和年份)get_earnings_calendar()  PS:这里可以指定比如说'NVDA'
6. 获取指定区间段发布财报的公司相关数据get_specific_time_period_earings_calendar()  PS：跟上面类似
7. 获取公司基本财务信息(比如PE、PS、52周最高/低价、流动比率、净利率、营收额) get_company_basic_financials()
8. 获取公司内部人士增/减持股票的相关信息get_stock_inside_transactions()
9. 获取公司内部人士情绪的相关信息get_stock_insider_sentiment()
10. 获取已报告的财务数据(包括财务报表) get_financials_reported()
11. 上市公司在SEC备案文件(一次不能超过250份)get_stock_filings()
目前我是通过定义获取函数的方式，并将得到的返回结果打印出来。

### V1.0版本——2025年10月18日正式开始
#### 如何从0开始创建一个项目
1. 首先在Github上点击【new】，首先给仓库起一个名字，注意Github会检测这个名字是否可用
2. 然后添加描述→选择仓库是公开or私人→是否添加README.md文件→是否添加.gitignore→是否添加License，这里会有一堆License让你选择，但一般选MIT或者Apache
3. 创建成功后，然后把仓库克隆到本地某个文件里，建议使用Git克隆到指定为止
4. 接下来可以使用VScode打开该项目，在【终端】创建venv虚拟环境，并激活。激活成功后，点开【终端】会发现前面带有一个(venv)。
5. 接着自己创建一个requirements.txt文件，用来记录项目依赖的第三方库清单，进而统一项目在不同环境中的依赖版本。
    格式为：库名==版本号#精确指定版本，比如pandas==2.1.5 库名>=最低版本 #允许高于某一个版 本，比如 Numpy>=1.26.3
6. 完成requirements.txt书写后，在【终端】执行 pip install -r requirements.txt。完成后，Python会按照清单中的库名和版本，自动下载并安装所有依赖。
7. 当你在整个项目里新增依赖的时候，使用pip freeze > requirements.txt，会将当前环境下所有已安装的第三方库及其版本写入文件中。执行后，打开requirements.txt也能看见所有依赖清单。

### 目前我准备先从基本面分析师Agent开始写
目前的项目流程图如下所示：
根目录
├── AI_Invest_Assistant
│   ├── Agents
│   │   └── fundamental_analyst.py
│   ├── web
│   │   └── streamlit.py
│   ├── .env
│   ├── .gitignore
│   ├── LICENSE
│   ├── main.py
│   ├── README.md
│   └── requirements.txt
└── venv