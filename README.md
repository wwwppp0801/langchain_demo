# 依赖
```
bash install_deps.sh
```

# webui
```
python3 webui.py
```

# 命令行执行单个query

```
##第一个参数是query，第二个参数是tool
python3 my_chain2.py '一个钱包里有100个五分和十分硬币。硬币的总价值是7美元。钱包里有多少个每种硬币？' 'search,wolframalpha_tool,python_coder,baidu_search'

```


# 命令行执行测试cases集合

```
##第一个参数是query，第二个参数是tool
python3 performance.py 'search,wolframalpha_tool,python_coder,baidu_search' 'upload/test_case.json'

```
test_case.json的样例可见[upload/test_case.json](upload/test_case.json)
