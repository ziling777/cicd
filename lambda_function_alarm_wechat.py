import json
import requests
import logging
import re
from urllib.parse import quote


logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    print(f"=====>event={event}")    
    """
    """
    wechatbot_urls = ['Change your webhook url'] 
    for url in wechatbot_urls:
        send_wechatbot(url, event)
    
    return {
        'statusCode': 200,
        'body': json.dumps('alarm message sent！')
    }


# 格式化SNS消息
def msg_format(event):
    try:
        # When the Lambda function is triggered by an SNS notification, the message payload will be included in the event parameter under $.Records[0].Sns.Message. 
        msg = event['Records'][0]['Sns']['Message']
        
        print(f"msg==========>{msg}")
        
       
        # msg = msg.replace("\\n", "\n")
        # if msg[0] == '\"' and msg[-1] == '\"':
        #     msg = msg[1:-1]
        result = re.sub(r'"phase-context": \[.*?\],', '', msg, flags=re.S)
        
        print(f"result=============>{result}")
        msg_json=json.loads(result)
        print(f"msg_json==========>{msg_json}")
        build_detail = msg_json['detail']
        print(f"build_detail==========>{build_detail}")
        # get build-id, 如：arn:aws:codebuild:eu-central-1:866665982863:build/prod-bigdata-dw-build:6b88fd03-70d6-4b95-9d87-03db3fcc915f
        build_id = build_detail['build-id']
        # get build status，如：IN_PROGRESS, SUCCEEDED, FAILED
        build_status = build_detail['build-status']
        # get codebuild project name
        build_name = build_detail['project-name']
        # get account
        account = msg_json['account']
        # 获得region
        region = msg_json['region']
        # 获得日志地址
        build_id_urlencode = quote(build_id.split(":build/")[-1])
        log_url = f"https://eu-central-1.console.aws.amazon.com/codesuite/codebuild/{account}/projects/{build_name}/build/{build_id_urlencode}/?region={region}"
        print(f"log_url==================>{log_url}")
        # get gitlab url
        gitlab_url = ''
        if 'additional-information' in build_detail and 'environment' in build_detail['additional-information'] and 'environment-variables' in build_detail['additional-information']['environment']:
            environment_variables = build_detail['additional-information']['environment']['environment-variables']
            print(f"environment_variables==================>{environment_variables}")
            for j in environment_variables:
                if j["name"] == "GIT_PROJECT_URL":
                    gitlab_url = j["value"]
        
        # message
        result = f"> Building Task Name：{build_name}\n> Building Task Log URL：{log_url}\n> Building Task Status：{build_status}\n> Code Repository URL：{gitlab_url}"
        return result
    except:
        # if the message is not from sns, return
        return event


# send message to wechatbot
def send_wechatbot(webhook_url,event):
    # format sns message
    msg = msg_format(event)
    print(msg)

    # wechat message format
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
            #print error when send failure  
            print(f" handle an error response from an API call  {response.status_code}: {response.text}")

    except:
        logger.error(f" handle an error response from an API call ，webhook url:{webhook_url} | content：{msg}")

