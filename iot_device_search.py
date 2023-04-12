import _env
import openai
openai.log="debug"
import os
import sys
import json


import plugin_profiles.profiles as profiles
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
plugin_name = "built-in/iot2.dueros.com"


embeddings = OpenAIEmbeddings(openai_api_key=_env.api_key)


persist_directory="./persist_directory/"+plugin_name
ruff_db=None
if os.path.exists(persist_directory):
    print("The path exists:"+persist_directory)
    ruff_db = Chroma(collection_name="device_db",persist_directory=persist_directory,embedding_function=embeddings)
else:
    print("The path does not exist:"+persist_directory)
    os.makedirs(persist_directory, exist_ok=True)
    profile = profiles.read_profile(plugin_name)
    device_list= profile["my_devices"]
    device_texts = [json.dumps(device,ensure_ascii=False) for device in device_list]
    device_metas = [device for device in device_list]
    print(device_texts)
    ruff_db = Chroma.from_texts(device_texts,embeddings,metadatas=device_metas, collection_name="device_db",persist_directory=persist_directory)
    ruff_db.persist()

query="工作日的早上九点半，打开客厅的空調"
docs=ruff_db.similarity_search(query)
print(docs)
doc_strings = [doc.page_content for doc in docs]
result="\n".join(doc_strings)
print(result)
