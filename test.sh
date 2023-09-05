#!/bin/bash

GIT_PROJECT_URL="https://git-devops.zeekrlife.com/bigdata/warehouse/demo_redshift_tpch.git"
GIT_BRANCH="prod"
GIT_PROJECT_IID=40
GIT_PROJECT_NAME="demo_redshift_tpch"
GIT_ACCESS_TOKEN="9FssyouuZfpt9yyXRMRf"
GIT_PROJECT_ID=9121

GIT_PROJECT_DOMAIN=${GIT_PROJECT_URL#*//}
GIT_PROJECT_DOMAIN=${GIT_PROJECT_DOMAIN%%/*}
echo "https://$GIT_PROJECT_DOMAIN/api/v4/projects/$GIT_PROJECT_ID/merge_requests/$GIT_PROJECT_IID/changes"

# 使用 curl 获取返回的json文件，并使用 jq 解压出增加和修改的文件  
ADD_MODIFIED_FILES=$(curl --header "PRIVATE-TOKEN: $GIT_ACCESS_TOKEN" "https://$GIT_PROJECT_DOMAIN/api/v4/projects/$GIT_PROJECT_ID/merge_requests/$GIT_PROJECT_IID/changes" | jq -c '.changes[] | select(.old_path | startswith("dags/")) | select(.new_file == true or .renamed_file == true or .modified_file == true) | .new_path')
echo "ADD_MODIFIED_FILES========>$ADD_MODIFIED_FILES"

DELETED_FILES=$(curl --header "PRIVATE-TOKEN: $GIT_ACCESS_TOKEN" "https://$GIT_PROJECT_DOMAIN/api/v4/projects/$GIT_PROJECT_ID/merge_requests/$GIT_PROJECT_IID/changes" | jq  -c '.changes[] | select(.old_path | startswith("dags/")) | select(.deleted_file == true or .renamed_file == true) | .old_path')
echo "DELETED_FILES========>$DELETED_FILES"

# 对新增或修改的DAG文件进行上传操作
for i in $ADD_MODIFIED_FILES
do
  local_file=${i//\"/}
  # 假设你希望在s3存储桶中保留/dags的目录结构
  echo "========>add file $MWAA_DBT_DIR$delfilename begin!"
  #aws s3 cp $local_file s3://$MWAA_DBT_DIR/MWAA_DAGS_DIR
done


# 对删除的DAG文件进行删除操作
for i in $DELETED_FILES
do
  s3_file=${i//\"/}
  echo "s3_file========>$s3_file"
  # delfilename=$(basename "$s3_file")
  # if aws s3 ls s3://$MWAA_DAGS_DIR$delfilename ; then
  #   echo "========>delete file $MWAA_DAGS_DIR$delfilename begin!"
  #   #aws s3 rm s3://$MWAA_DAGS_DIR$delfilename
  #   #echo "========>delete file $MWAA_DAGS_DIR$delfilename end!"
  # fi
done