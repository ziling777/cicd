FROM AWS_CCOUNT.dkr.ecr.AWS_REGION.amazonaws.com/cosmos-dbt-base:1.0

ENV AWS_DEFAULT_REGION "AWS_REGION"

# 设置工作目录
WORKDIR /app

# 复制dbt项目文件到容器中
COPY . /app

RUN dbt deps
#RUN dbt compile --profiles-dir .
#RUN dbt build --profiles-dir .

# 运行dbt命令
#ENTRYPOINT /bin/bash
