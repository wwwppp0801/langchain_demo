import sys
import os
import json
import zipfile
import yaml
import subprocess

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

def run_python_code(filename):
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
    import _env
    #print([_env.python_path,filename])
    p = subprocess.Popen([_env.python_path,filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    output = out.decode() + err.decode()
    if output.strip(" \t\n")=="":
        output="no print out answers"
    return output

def read_profile(profile_name):
    dirname=os.path.dirname(os.path.abspath(__file__))+"/"+profile_name
    if not os.path.exists(dirname):
        log=f'No profile found: {dirname}'
        print(log)
        raise FileNotFoundError(log)
    files={
            "manifest_doc":"manifest.json",
            "api_doc":"api.yaml",
            "my_devices":"device_list.json",
            "devices_db":"devicelist_detail.txt",
            }
    result={}
    for key in files.keys():
        file=f'{dirname}/{files[key]}'
        if not os.path.exists(file):
            log=f'No {file} file found: {file}'
            print(log)
            raise FileNotFoundError(log)
        result[key]=read_file(file)

    # read system prompts
    prompt_py=f'{dirname}/prompt'
    #print(prompt_py)
    if os.path.exists(prompt_py):
        try:
            prompt_raw=run_python_code(prompt_py)
            prompt=json.loads(prompt_raw)
            result["prompt"]=prompt
        except Exception as e:
            print(e,file=sys.stderr)

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



