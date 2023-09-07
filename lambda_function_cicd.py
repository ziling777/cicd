
import json
import boto3
import os

def lambda_handler(event, context):
    print(f"event = {event}")
    codebuild = boto3.client('codebuild')
    secrets = boto3.client('secretsmanager')
    
    body = json.loads(event['body'])
    print(f"body==={body}")
    
    # 只处理prod或uat，暂时只有prod
    target_branch = body['object_attributes']['target_branch']
    if target_branch != 'prod':
        print ("=====> The git branch does not match, it needs to be the prod branch.")
        return {'statusCode': 403, 'body': 'The git branch does not match, it needs to be the prod branch.'}
        
    # 通过token校验事件接收权限，token的校验值放在secrets manager中
    secretValues = secrets.get_secret_value(SecretId=os.environ['SECRET_MANAGER_KEY'])['SecretString']
    dic_secrets = json.loads(secretValues)
    
    #获得webhook_token并进行验证
    git_project_id = str(body['project']['id'])
    project_info_key = 'project_info_' + git_project_id
    secret_project_info_json_str = dic_secrets[project_info_key]
    project_info = json.loads(secret_project_info_json_str)
    webhook_token = project_info['webhook_token']
    if event['headers'].get('x-gitlab-token',event['headers'].get('X-Gitlab-Token')) != webhook_token:
        print ("=====> No permission, Bad Token!")
        return {'statusCode': 401, 'body': 'Bad Token'}

  
    # 校验参数  
    if 'object_attributes' not in body or 'action' not in body['object_attributes']:
        print ("=====> No permission, No action field!")
        return {'statusCode': 403, 'body': 'No action field!'}
        

    
    # 只处理merge_request事件且MR的action为merge时才进行处理
    event_type = body['event_type']
    mr_action = body['object_attributes']['action']
    print(f"=====> event_type={event_type} | target_branch={target_branch} ｜ mr_action={mr_action}")
    if  event_type != 'merge_request' or mr_action != 'merge':
        print ("=====>No permission, Processing is stopped because the target branch or event type does not satisfy the condition!")
        return {'statusCode': 403, 'body': 'Does not satisfy the condition'}
 
    # 工程http地址
    git_project_url = body['project']['git_http_url']
    # 工程名称
    git_project_repo = body['repository']['name']
    git_access_token = project_info['git_access_token']
    git_project_iid = str(body['object_attributes']['iid'])
    print(f"=====>git_project_id={git_project_id}| git_project_url={git_project_url} | git_project_repo={git_project_repo} ｜ event_type={event_type} | target_branch={target_branch}")
    # 启动codeBuild
    codebuild.start_build(
        projectName='prod-bigdata-dw-build',
        environmentVariablesOverride=[
            {
                'name': 'GIT_PROJECT_URL',
                'value': git_project_url,
                'type': 'PLAINTEXT'
            },
            {
                'name': 'GIT_PROJECT_NAME',
                'value': git_project_repo,
                'type': 'PLAINTEXT'
            },
            {
                'name': 'GIT_ACCESS_TOKEN',
                'value': git_access_token,
                'type': 'PLAINTEXT'
            },
            {
                'name': 'GIT_PROJECT_ID',
                'value': git_project_id,
                'type': 'PLAINTEXT'
            },
            {
                'name': 'GIT_PROJECT_IID',
                'value': git_project_iid,
                'type': 'PLAINTEXT'
            }
        ]
    )
    
    print ("=====>build end")

    return {
        'statusCode': 200,
        'body': json.dumps('调用codebuild成功')
    }