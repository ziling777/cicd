
import json
import boto3
import os

def lambda_handler(event, context):
    print(f"event = {event}")
    codebuild = boto3.client('codebuild')
    secrets = boto3.client('secretsmanager')
    
    # 通过token校验事件接收权限，token的校验值放在secrets manager中
    secretValues = secrets.get_secret_value(SecretId=os.environ['SECRET_WEBHOOK_ARN'])['SecretString']
    dic_secrets = json.loads(secretValues)
    # gitlab webhook token
    git_webhook_token = dic_secrets['gitlab-webhook-token']
    if event['headers'].get('x-gitlab-token',event['headers'].get('X-Gitlab-Token')) != git_webhook_token:
        print ("=====> No permission!")
        return {'statusCode': 401, 'body': 'Bad Token'}
    
    
    body = json.loads(event['body'])
    # 工程http地址
    git_project_url = body['project']['git_http_url']
    # 工程名称
    git_project_repo = body['repository']['name']
    # 工程ID
    git_project_id = body['repository']['id']
    # 事件类型
    event_type = body['event_type']
    # MR的目标分支
    target_branch = body['object_attributes']['target_branch']
    # MR action
    mr_action = body['object_attributes']['action']
    
    print(f"=====> event_type={event_type} | target_branch={target_branch} ｜ mr_action={mr_action}")
    
    # 校验MR的目标分支
    if  event_type != os.environ['EVENT_TYPE'] or target_branch != os.environ['TARGET_BRANCH'] or mr_action != 'merge':
        print ("=====> Processing is stopped because the target branch or event type does not satisfy the condition!")
        return {'statusCode': 403, 'body': 'Does not satisfy the condition'}
    
    print(f"=====> git_project_url={git_project_url} | git_project_repo={git_project_repo} ｜ event_type={event_type} | target_branch={target_branch}")
    
    # 启动codeBuild
    # command = os.environ['COMMAND']
    # projectName = os.environ['CODEBUILD_PROJECT_NAME']
    # gitlab project token
    project_token_key = "project_token_"+git_project_id
    git_project_token = dic_secrets[project_token_key]
    # 项目的merge reqeust id
    git_project_merge_reqeust_id = body['object_attributes']['iid']
    
    print(f"=====> git_project_token={git_project_token} | git_project_id={git_project_id}")
    
    codebuild.start_build(
        projectName='dbt-build-new2',
        environmentVariablesOverride=[
            {
                'name': 'GIT_PROJECT_URL',
                'value': new_url,
                'type': 'PLAINTEXT'
            },
            {
                'name': 'GIT_PROJECT_NAME',
                'value': git_project_repo,
                'type': 'PLAINTEXT'
            },
            {
                'name': 'GIT_ACCESS_TOKEN',
                'value': git_project_token,
                'type': 'PLAINTEXT'
            },
            {
                'name': 'GIT_PROJECT_ID',
                'value': git_project_id,
                'type': 'PLAINTEXT'
            },
             {
                'name': 'GIT_PROJECT_IID',
                'value': git_project_merge_reqeust_id,
                'type': 'PLAINTEXT'
            }
            
        ]
    )

    return {
        'statusCode': 200,
        'body': json.dumps('调用codebuild成功')
    }