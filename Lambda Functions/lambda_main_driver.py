import json
import boto3
import pandas as pd
from io import StringIO
import hashlib
from datetime import datetime
import os
import time
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    read_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    document = event["Records"][0]["s3"]["object"]["key"]
    s3_client = boto3.client("s3")
    s3 = boto3.resource("s3")
    s3_dynamo = boto3.resource('dynamodb')
    client = boto3.client('textract')
    
    #Get the MD5 hash of the Image Uploaded
    s3_resp = s3_client.head_object(Bucket=read_bucket, Key=document)
    s3obj_etag = s3_resp['ETag'].strip('"')
    print(s3obj_etag)
    
    s3_email = s3_resp['Metadata']['email']
    print(s3_email)
    
    #We will then compare this against our DynamoDB Database
    table = s3_dynamo.Table('HardCodersDB')
    db_response = table.get_item(Key={ 'MD5':s3obj_etag})
       
    #Flag for calling Textract 
    flag = 0
    
    if 'Item' in db_response:
        #If the file already exists, return the stored JSON dictionary
        content_object = s3_client.get_object(Bucket=db_response['Item']['bucketpointer'],Key=db_response['Item']['filepointer'])
        #We will dump json_content for the front end
        json_content = content_object['Body'].read().decode()
        print("file exists")
    else:
        #Else, the file doesn't exist, set flag to call TextTract
        flag = 1
        print('File does not exist! Calling TextTract!')
    ##################################################################
    
    if (flag == 1):
        #GET the S3 Object for Textract
        response = client.detect_document_text(
            Document={'S3Object':{'Bucket':read_bucket,'Name':document}})
            
        #Get the text blocks
        blocks = response['Blocks']
        
        words = []
        confidences = []
        
        for block in blocks:
            if block['BlockType'] == "WORD":
                words.append(block['Text'])
                confidences.append(block['Confidence'])
        
        my_data={'Word':words,'Confidence Level':confidences}
        df = pd.DataFrame(data=my_data)
        #Clean up by removing punctuation from the words
        df['Word'] = df['Word'].str.extract('(\w+)', expand = False)
    
        #Write to CSV
        write_bucket = "hardcoders-back-end"
        csv_buffer = StringIO()
        df.to_csv(csv_buffer)
        
        s3_resource = boto3.resource('s3')
        #Strip off the file extension
        file_name = os.path.splitext(document)[0]
        s3_resource.Object(write_bucket, str(s3obj_etag) + '*' + str(datetime.now().strftime("%m_%d_%Y_%H_%M_%S")) + '.csv').put(Body=csv_buffer.getvalue()) #Use * as a seperator
    
    
    #Delete the picture
    object_to_be_deleted = s3.Object(read_bucket, document)
    object_to_be_deleted.delete()
    
    second_flag = 0
    #Deal with waiting for DynamoDB Entry for new images
    timeout = time.time() + 60*5  #5 Minute from now
    if(flag == 1):
        
        while True:
            db_response = table.get_item(Key={ 'MD5':s3obj_etag})
            
            #Check DynamoDB for MD5 Hash value
            if 'Item' in db_response and time.time() < timeout:
                second_flag = 1
                break
            elif 'Item' not in db_response and time.time() > timeout:
                break
        
            print('Waiting...')
            #Poll every 2 second
            time.sleep(2)
        
        if(second_flag == 1):
            db_response = table.get_item(Key={ 'MD5':s3obj_etag})
            content_object = s3_client.get_object(Bucket=db_response['Item']['bucketpointer'],Key=db_response['Item']['filepointer'])
            json_content = content_object['Body'].read().decode()
            print('got content!')
        else:
            json_content = {'Error':'Timed Out. Try Again!'}
            print('Timed out')
    
        
        #Preapre for SES Email of Results
    
    SENDER = "fey432@gmail.com"
    RECIPIENT = s3_email
    AWS_Region = "us-east-1"
    CHARSET = "UTF-8"
    mail_client = boto3.client('ses',region_name=AWS_Region)
    
    if(flag == 1 and second_flag == 0):
        SUBJECT = "Error Trying to Get Your Results"
        BODY_TEXT = "There was an error trying to get your results. Please try to upload again!"
        try:
            email_response = mail_client.send_raw_email(
                Destination={
                    'ToAddresses':[
                        RECIPIENT,
                    ],
                },
                Message = {
                    'Body':{
                        'Text':{
                            'Charset':CHARSET,
                            'Data' : SUBJECT
                            }
                    },
                    'Subject':{
                        'Charset' : CHARSET,
                        'Data' : SUBJECT
                    }
                },
                    Source = SENDER
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email sent!")
    else:
        SUBJECT = "Your OCR Results are Available"
        BODY_TEXT = "Hello,\r\nYour OCR Word Count Reduce Results are ready! Please see the attached JSON File\r\nSincerely,\r\nHard Coders"
        
        #Temp dump 
        base_name = os.path.basename(db_response['Item']['filepointer'])
        tmp_file_name = '/tmp/' + base_name
        s3_client.download_file(db_response['Item']['bucketpointer'],db_response['Item']['filepointer'],tmp_file_name)
        attachment = tmp_file_name

        msg = MIMEMultipart('mixed')
        # Add email contents
        msg['Subject'] = SUBJECT
        msg['From'] = SENDER
        msg['To'] = RECIPIENT
        msg_body = MIMEMultipart('alternative')
        textpart = MIMEText(BODY_TEXT.encode(CHARSET),'plain',CHARSET)
        msg_body.attach(textpart)
        att = MIMEApplication(open(attachment,'rb').read())
        att.add_header('Content-Disposition','attachment',filename=os.path.basename(attachment))
        msg.attach(msg_body)
        msg.attach(att)
    
        try:
            email_response = mail_client.send_raw_email(
                Source=SENDER,
                Destinations=[
                    RECIPIENT
                    ],
                    RawMessage={
                        'Data':msg.as_string(),
                    },
            )
        except ClientError as e:
            print("Error sending email")
            print(e.response['Error']['Message'])
        else:
            print("Email sent! Message ID: ")
            print(email_response['MessageId'])

    
    
    