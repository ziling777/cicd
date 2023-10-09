FROM python:3.9-slim

# 安装所需依赖
RUN apt-get update

# 设置工作目录
WORKDIR /base

COPY ./requirements.txt /base

RUN pip install -U pip \
    && pip --no-cache-dir install -r ./requirements.txt

# 运行dbt命令
#ENTRYPOINT dbt --version