import json
import boto3


def lambda_handler(event, context):
    #Get the Bucket Name
    read_bucket = event["Records"][0]["s3"]["bucket"]["name"]   #This should be hardcoders-back-end
    
    #Get the Folder Name
    folder = event["Records"][0]["s3"]["object"]["key"]       #This should be [md5][date].json folder
    
    client = boto3.client('s3')
    
    #Get the Folder and the Single File
    response = client.list_objects_v2(Bucket = read_bucket, Prefix = folder)
    
    #Grab the MD5 Value for the MD5 attribute for DynamoDB
    MD5_value = response['Prefix'].split('*')[0]
    
    #Create Item in DynamoDB
    db_client = boto3.client('dynamodb')
    
    data = db_client.put_item(
        TableName='HardCodersDB',
        Item={
            'MD5':{
                'S': MD5_value
            },
            'bucketpointer':{
                'S': read_bucket
            },
            'filepointer':{
                'S': response['Prefix']
            }
        }
    )
    
   
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps(data)
    }
