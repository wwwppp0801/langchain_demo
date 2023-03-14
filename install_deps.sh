

# 依赖

pip3 install langchain==0.0.100  -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install openai  -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install google-search-results  -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install wolframalpha  -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install nltk  -i https://pypi.tuna.tsinghua.edu.cn/simple

# PythonCoder依赖
pip3 install sympy  -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install wikipedia -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install bs4 -i https://pypi.tuna.tsinghua.edu.cn/simple


# webui依赖

pip3 install flask
pip3 install flask_socketio  -i https://pypi.tuna.tsinghua.edu.cn/simple


# 文件搜索依赖
pip3 install "unstructured[local-inference]" -i https://pypi.tuna.tsinghua.edu.cn/simple

pip3 install 'git+https://github.com/facebookresearch/detectron2.git' -i https://pypi.tuna.tsinghua.edu.cn/simple

pip3 install libmagic -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install chromadb -i https://pypi.tuna.tsinghua.edu.cn/simple

os=$(uname -s)
if [ "$os" = "Linux" ]; then
    echo "This is Linux"
elif [ "$os" = "Darwin" ]; then
    echo "This is Mac OS X"
    brew install poppler
    brew install libmagic
else
    echo "Unknown OS"
fi
