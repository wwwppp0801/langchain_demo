import sys
import os
import json
import zipfile
import yaml

def read_file(filename):
    """read file"""
    try:
        with open(filename, 'r') as file:
            documents = yaml.load(file, Loader=yaml.FullLoader)
            return documents
    except Exception as e:
        None

    try:
        with open(filename, 'r') as file:
            documents = json.loads(file.read())
            return documents
    except Exception as e:
        None

    raise Exception(f"can not read file {filename}")

def read_profile(profile_name):
    dirname=os.path.dirname(os.path.abspath(__file__))+"/"+profile_name
    files={
            "manifest_doc":"manifest.json",
            "api_doc":"api.yaml",
            "device_list":"device_list.json"
            }
    result={}
    for key in files.keys():
        file=f'{dirname}/{files[key]}'
        if not os.path.exists(file):
            log=f'No {file} file found: {file}'
            print(log)
            raise FileNotFoundError(log)
        result[key]=read_file(file)
    return result

def unzip_file_to_proile(zip_path):
    # 读取压缩文件
    file = zipfile.ZipFile(zip_path)
    # 从完整路径中获取文件名
    profile_name = os.path.basename(zip_path)
    # 解压文件
    save_path = os.path.dirname(os.path.abspath(__file__))+"/"+profile_name
    # 如果文件夹不存在则创建
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    file.extractall(save_path)
    # 关闭文件流
    file.close()



