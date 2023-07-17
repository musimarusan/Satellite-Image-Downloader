# [References]
# https://sites.google.com/site/mizuochipublic/実践コンテンツ/google-earth-engine入門/6-pythonによるローカルからのgee実行?authuser=0
# https://colab.research.google.com/github/csaybar/EEwPython/blob/dev/10_Export.ipynb

import os
import pandas as pd
from io import BytesIO
import ee 
from google.auth import compute_engine, impersonated_credentials
from google.cloud import storage
from dateutil.parser import parse


####
####
ee.Initialize(credentials)


# function : make Cloud Mask using QA60
# image(in):image collection
def cloudMasking(image):
    qa = image.select('QA60')
    cloudBitMask = 1 << 10  
    cirrusBitMask = 1 << 11
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
    return image.updateMask(mask).divide(10000)


# function        : image exporting
# image(in)       : image collection
# description(in) : output image name
# scale(in)       : spatial resolution
# fileFormat(in)  : file format of output imagery
# bucket          : GSC bucket name for file output
def ImageExport(image, description, scale, region, fileFormat, bucket):
    task = ee.batch.Export.image.toCloudStorage(**{
        'image': image,
        'description': description,
        'scale': scale,
        'region': region,
        'fileFormat': fileFormat,
        'bucket': bucket,
        'formatOptions': {'cloudOptimized': True}        
    })
    task.start()

# function :
# imageList(in) : list of image collection
def ExportIteration(imageList, scale_in, bucket_in):

    imgList = []
    bucket = storage_client.bucket(bucket_in)
    blobs  = storage_client.list_blobs(bucket)
    for blob in blobs:
        imgList.append(blob.name)

    for ii in range(imageList.size().getInfo()):
        image          = ee.Image(imageList.get(ii))
        image_in       = image.reproject(crs='EPSG:4326',scale=10)
        description_in = image.get('system:index').getInfo()
        region_in      = region.getInfo()['coordinates']
        fileformat_in  = 'GeoTIFF'

        filename = description_in + '.tif'
        if filename in imgList:
            print(ii, description_in, 'already exists.')
        else:
            ImageExport(image_in, description_in, scale_in, region_in, fileformat_in, bucket_in)
            print(ii, description_in, 'was created.')
            
    print('finish :', bucket_in)



# AOI definition
region=ee.Geometry.Rectangle([130.435266,32.942276,130.497408,32.898326])

# Constants. They will be define in parameter setting py script.
BAND  = 'B1'
SCALE = 10
SDATE = '2022-01-01'
EDATE = '2022-12-31'

# get image cpllection
S2_Image  = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(region).filterDate(parse(SDATE),parse(EDATE)).map(cloudMasking).select([BAND])
ImageList = S2_Image.toList(300)

# comfirm bucket existence
storage_client  = storage.Client.from_service_account_json('.private-key.json')
bucket_name = 's2_ms_' + BAND.lower()
gcs_buckets = storage_client.list_buckets()
gcs_bucket_list = []
for blob in gcs_buckets:
    gcs_bucket_list.append(blob.name)

if bucket_name in gcs_bucket_list:
    print(bucket_name, 'already exists.')
else:
    bucket = storage_client.create_bucket(bucket_name)
    print('newly created', bucket_name)
    
# image creation
ExportIteration(ImageList, SCALE, bucket_name)


print('Program sucessfully finished.')
