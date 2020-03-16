#!/bin/bash

LAMBDA_FOLDER="lambda"
BUILD_FOLDER="lambda_build"

echo -e "\n*** Removing existing build folder\n"

echo $BUILD_FOLDER
rm -rf $BUILD_FOLDER

echo -e "\n*** Copying lambda files to build folder ...\n"

rsync -avr --exclude=**/.ipynb_checkpoints --exclude=**/__pycache__ $LAMBDA_FOLDER/* $BUILD_FOLDER

echo -e "\n*** Launching docker container to install dependencies from requirements.txt\n"

docker container run \
    --rm \
    --user $(id -u):$(id -g) \
    -v $(pwd)/$BUILD_FOLDER:/var/task \
    lambci/lambda:build-python3.7 \
    /bin/sh -c 'python3.7 -m pip install --no-cache-dir --target /var/task/ --requirement /var/task/requirements.txt && find /var/task/ -name "*.so" -exec strip {} \;'

echo -e "\n*** Removing files to be excluded from the deploy\n"

declare -a EXCLUDE_PATTERNS=("boto3*" "botocore*" "docutils*" "jmespath*" "pip*" "python-dateutil*" "s3transfer*" "setuptools*" 
                             "*.dist-info" "__pycache__" "*.pyc" "*.pyo")

for i in "${EXCLUDE_PATTERNS[@]}"
do
   find $BUILD_FOLDER -name "$i" -prune -print -exec rm -rf "{}" \;
done
