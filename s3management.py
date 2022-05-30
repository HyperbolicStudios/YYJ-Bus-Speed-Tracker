import boto3
import os
from inspect import getsourcefile
from os.path import abspath

#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

s3 = boto3.resource(
    service_name='s3',
    region_name='us-east-2',
    aws_access_key_id='AKIAT3D7YDXK3TOCKF72',
    aws_secret_access_key='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'
)
# Upload files to S3 bucket
s3.Bucket('busspeedbucket').upload_file(Filename='mapping.py', Key='mapping.py')
"""
# Download file and read from disc
s3.Bucket('cheez-willikers').download_file(Key='foo.csv', Filename='foo2.csv')
pd.read_csv('foo2.csv', index_col=0)"""
