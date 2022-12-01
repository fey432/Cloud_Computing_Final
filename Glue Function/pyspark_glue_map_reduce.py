import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import boto3

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME','bucket_name','file_name'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

#TODO
s3_file_path = "s3://" + str(args['bucket_name']) + "/" + str(args['file_name'])
df = spark.read.format("csv").option("header","true").load(s3_file_path)
df = df.withColumn("Word",lower(col("Word")))
df = df.groupBy('Word').count()
df = df.sort(desc('count'))

#We will need to change the folder name of the JSON file to the Unique identifier
#Take off the .csv from the filename. Remove last 4 characters
file_name = args['file_name']
file_name = file_name[:-4]
df.coalesce(1).write.format('json').save('s3://hardcoders-back-end/' + str(file_name) + '.json')

#Delete the CSV file_name
s3 = boto3.resource('s3')
object_to_be_deleted = s3.Object(args['bucket_name'], args['file_name'])
object_to_be_deleted.delete()
job.commit()