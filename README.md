# AI_Invest_Assistant
An AI investment assistant based on a large language model



## V 1.0版本——2025年10月18日正式开始
### 如何从0开始创建一个项目
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