import json
import os
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Import Boto3 for AWS Glue
import boto3
client = boto3.client('glue')

#Variables for the job:
glueJobName = "PySpark_MapReduce"


def lambda_handler(event, context):
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    document = event["Records"][0]["s3"]["object"]["key"]
    response = client.start_job_run(JobName = glueJobName, Arguments = {'--bucket_name': bucket,'--file_name':document})
    logger.info('## STARTED GLUE JOB: ' + glueJobName)
    logger.info('## GLUE JOB RUN ID: ' + response['JobRunId'])
    
    return response
