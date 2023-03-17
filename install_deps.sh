
suffix=" -i https://pypi.tuna.tsinghua.edu.cn/simple"

# 依赖

pip3 install langchain==0.0.100  $suffix
pip3 install openai  $suffix
pip3 install google-search-results  $suffix
pip3 install wolframalpha  $suffix
pip3 install nltk  $suffix

# PythonCoder依赖
pip3 install sympy  $suffix
pip3 install wikipedia $suffix
pip3 install bs4 $suffix


# webui依赖

pip3 install flask
pip3 install flask_socketio  $suffix

#performance.sh依赖
pip3 install pandas $suffix
pip3 install openpyxl $suffix


# 文件搜索依赖
pip3 install "unstructured[local-inference]" $suffix

pip3 install 'git+https://github.com/facebookresearch/detectron2.git'

pip3 install libmagic $suffix
pip3 install chromadb $suffix

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
