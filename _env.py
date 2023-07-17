import os
import configparser
# 创建一个ConfigParser对象
config = configparser.ConfigParser()
dirname = os.path.dirname(os.path.realpath(__file__))
# 读取一个INI文件
config.read(f"{dirname}/config.ini")

# 设置组织ID和API密钥
#openai.organization=config.get("main", "organization")
model_name=config.get("main", "model")
model=config.get("main", "model")

google_search_api_key=config.get("main","google_search_api_key")
openai_api_base=config.get("main","openai_api_base",fallback=None)
organization=config.get("main", "organization")
api_key=config.get("main", "api_key")
wolframalpha_appid=config.get("main","wolframalpha_appid")
baidu_trans_app_id=config.get("main","baidu_trans_app_id")
baidu_trans_secret_key=config.get("main","baidu_trans_secret_key")

proxy_logger_host=config.get("main","proxy_logger_host",fallback=None)
proxy_logger_port=int(config.get("main","proxy_logger_port",fallback="0"))
use_proxy_logger=config.get("main","use_proxy_logger",fallback=None)
proxy_default_backend_server=config.get("main","proxy_default_backend_server",fallback=None)

embedding_search=config.get("main","embedding_search",fallback=None)

python_path=config.get("main","python_path")
host=config.get("main","host")
port=config.get("main","port")

plugin_base_url = config.get("main","plugin_base_url",fallback=None)

azure = config.get("main","azure",fallback=None)
azure_end_point = config.get("main","azure_end_point",fallback=None)
azure_api_key = config.get("main","azure_api_key",fallback=None)
azure_deploy = config.get("main","azure_deploy",fallback=None)

### 少锋的代理
if azure:
    import openai
    #openai.api_key = os.getenv("AZURE_OPENAI_KEY")
    openai.api_key = azure_api_key
    api_key=azure_api_key
    #openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT") # your endpoint should look like the following https://YOUR_RESOURCE_NAME.openai.azure.com/
    openai.api_base = azure_end_point # your endpoint should look like the following https://YOUR_RESOURCE_NAME.openai.azure.com/
    openai.api_type = 'azure'
    openai.api_version = '2023-05-15' # this may change in the future
elif openai_api_base:
    if "OPENAI_API_BASE" not in os.environ:
        os.environ["OPENAI_API_BASE"]=openai_api_base
    import openai
    openai.api_key="xxxxxxxxxxx"
else:
    import openai
    #openai.organization=config.get("main", "organization")
    openai.api_key=config.get("main", "api_key")
