import os
import boto3
import json
from datetime import datetime
from pathlib import Path

from airflow.decorators import dag
from airflow.operators.empty import EmptyOperator

from cosmos.providers.dbt import DbtTaskGroup

from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
#from kubernetes.client import V1EnvVar
#from kubernetes.client import V1ResourceRequirements
#test



@dag(
    schedule_interval="@daily",
    start_date=datetime(2023, 7, 24),
    catchup=False,
)
def basic_eks_cosmos_task_group() -> None:
    
    def get_prod_redshift_bi_conn_json():
        secrets = boto3.client('secretsmanager')
        secretValues = secrets.get_secret_value(SecretId="redshiftserverless")['SecretString']
        dic_secrets_json = json.loads(secretValues)
       # prod_redshift_bi_str = dic_secrets_json['prod_redshift_bi']
       # prod_redshift_bi_json = json.loads(dic_secrets_json)
        return dic_secrets_json

    

    prod_redshift_bi_conn=get_prod_redshift_bi_conn_json()
   

    pre_dbt = EmptyOperator(task_id="pre_dbt")


    _project_dir= "/usr/local/airflow/dags/dbt_projects_dir/"

    # tolerations = [{
    #     'key': 'app',
    #     'operator': 'Equal',
    #     'value': 'bigdata-dw',
    #     'effect': 'NoSchedule'
    # }]

    # nodeSelector = {
    #     'app': 'bigdata-dw'
    # }

    # resources = V1ResourceRequirements(
    #     requests={"memory": "8Gi", "cpu": "4"},
    #     limits={"memory": "8Gi", "cpu": "4"}
    # )


    redshift_dbt_group = DbtTaskGroup(
        dbt_root_path=_project_dir,
        dbt_project_name="dbtcicd",
        execution_mode="kubernetes",
        conn_id="bi-poc-redshift",
        select={"configs": ["tags:finance"]},
        operator_args={
            "do_xcom_push": False,
            "project_dir":"/app",
            "namespace":"prod-bigdata-dw-mwaa",
            "image": "082526546443.dkr.ecr.us-east-2.amazonaws.com/cicd:prod",
            "get_logs": True,
            "is_delete_operator_pod": True,
           # "labels": {"app": "bigdata-dw"},
            "name": "mwaa-cosmos-pod-dbt",
            "config_file": "/usr/local/airflow/dags/kubectl.config",
            "in_cluster": False,
            "vars": '{"my_car": "val1"}',
            "env_vars": {"TARGT": "prod_password",
                         "DB_HOST": prod_redshift_bi_conn['host'], 
                         "DB_PORT": str(prod_redshift_bi_conn['port']), 
                         "DB_USER": prod_redshift_bi_conn['username'],
                         "DB_PASSWORD": prod_redshift_bi_conn['password'],
                         "DB_NAME": prod_redshift_bi_conn['dbname'],
                         "DB_SCHEMA": prod_redshift_bi_conn['schema']
                        },
            # service_account_name当IAM连接Redshift时使用
            #"service_account_name": "prod-bigdata-bi-redshift-iam-sa",        
            #"cluster_context": "aws",
            "image_pull_policy": "Always",
           # "tolerations": tolerations,
            #"node_selector": nodeSelector
            #"resources": resources
        },
    )

    post_dbt = EmptyOperator(task_id="post_dbt")

    submit_glue_job = GlueJobOperator(
        task_id="test-etl2",
        job_name="test-etl2",
        script_location=f"s3://aws-glue-assets-082526546443-us-east-2/scripts/test-etl2.py",
        s3_bucket="aws-glue-assets-082526546443-us-east-2",
        iam_role_name="AWSGlueServiceRole-test",
         create_job_kwargs={
            "GlueVersion": "4.0", 
            "NumberOfWorkers": 2, 
            "WorkerType": "G.1X", 
            "Connections":{"Connections":["redshift"]},
            "DefaultArguments": {
                "--enable-auto-scaling": "true",
                "--max-num-workers": "10",
                "--enable-metrics": "true",
                "--metrics-sample-rate": "1",
                "--job-bookmark-option": "job-bookmark-disable",
                "--enable-continuous-cloudwatch-log": "true",
                "--log-level": "INFO",
                "--enable-glue-datacatalog": "true",
                "--enable-spark-ui": "true",
                "--enable-job-insights": "true",
                "--TempDir": "s3://aws-glue-assets-082526546443-us-east-2/temporary/",
                "--spark-event-logs-path": "s3://aws-glue-assets-082526546443-us-east-2/sparkHistoryLogs/"
                }
         }
    )

    pre_dbt >> submit_glue_job >> redshift_dbt_group >> post_dbt



basic_eks_cosmos_task_group()

