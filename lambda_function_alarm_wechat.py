import json
import requests
import logging
import re
from urllib.parse import quote

# Lambda日志只记录标准输出流，所以不使用logging
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    print(f"=====>event={event}")    
    """
    EU-数仓-生产CICD通知机器人:https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=6c0007b2-c343-43f9-811e-a4144a1dbc2b
    """
    wechatbot_urls = ['https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=6c0007b2-c343-43f9-811e-a4144a1dbc2b'] 
    for url in wechatbot_urls:
        send_wechatbot(url, event)
    
    return {
        'statusCode': 200,
        'body': json.dumps('企业微信告警消息发送完成！')
    }


# 格式化SNS消息
def msg_format(event):
    try:
        # 消息来源是SNS，取 $.Records[0].Sns.Message，并对字符串进行一些处理，确保发送时可以正常显示
        msg = event['Records'][0]['Sns']['Message']
        
        print(f"msg==========>{msg}")
        
        # # 进行字符串处理后返回，以确保IM客户端正确显示
        # msg = msg.replace("\\n", "\n")
        # if msg[0] == '\"' and msg[-1] == '\"':
        #     msg = msg[1:-1]
        result = re.sub(r'"phase-context": \[.*?\],', '', msg, flags=re.S)
        
        print(f"result=============>{result}")
        msg_json=json.loads(result)
        print(f"msg_json==========>{msg_json}")
        build_detail = msg_json['detail']
        print(f"build_detail==========>{build_detail}")
        # 获得build-id, 如：arn:aws:codebuild:eu-central-1:866665982863:build/prod-bigdata-dw-build:6b88fd03-70d6-4b95-9d87-03db3fcc915f
        build_id = build_detail['build-id']
        # 获得构建状态，如：IN_PROGRESS, SUCCEEDED, FAILED
        build_status = build_detail['build-status']
        # 获得构建名称
        build_name = build_detail['project-name']
        # 获得account
        account = msg_json['account']
        # 获得region
        region = msg_json['region']
        # 获得日志地址
        build_id_urlencode = quote(build_id.split(":build/")[-1])
        log_url = f"https://eu-central-1.console.aws.amazon.com/codesuite/codebuild/{account}/projects/{build_name}/build/{build_id_urlencode}/?region={region}"
        print(f"log_url==================>{log_url}")
        # 获得被编译代码的仓库地址
        gitlab_url = ''
        if 'additional-information' in build_detail and 'environment' in build_detail['additional-information'] and 'environment-variables' in build_detail['additional-information']['environment']:
            environment_variables = build_detail['additional-information']['environment']['environment-variables']
            print(f"environment_variables==================>{environment_variables}")
            for j in environment_variables:
                if j["name"] == "GIT_PROJECT_URL":
                    gitlab_url = j["value"]
        
        # 组装微信消息
        result = f"> Building Task Name：{build_name}\n> Building Task Log URL：{log_url}\n> Building Task Status：{build_status}\n> Code Repository URL：{gitlab_url}"
        return result
    except:
        # 消息来源不是SNS，直接返回
        return event


# 发送消息到企业微信机器人
def send_wechatbot(webhook_url,event):
    # 格式化SNS消息
    msg = msg_format(event)
    print(msg)

    # 企业微信消息格式
    data = {
        "msgtype": "text",
        "text": {
            "content": msg
        }
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(
            webhook_url, 
            data=json.dumps(data),
            headers=headers
        )
        if response.status_code != 200:
            #发送失败只打印错误日志不抛异常   
            print(f"请求到企业微信 API返回错误 {response.status_code}: {response.text}")

    except:
        logger.error(f"请求到企业微信 API失败！请求url:{webhook_url} | 发送内容：{msg}")

