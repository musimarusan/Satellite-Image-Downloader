# [References]
# https://sites.google.com/site/mizuochipublic/実践コンテンツ/google-earth-engine入門/6-pythonによるローカルからのgee実行?authuser=0
# https://colab.research.google.com/github/csaybar/EEwPython/blob/dev/10_Export.ipynb

import sys
import os
import datetime
import pandas as pd
from io import BytesIO
import ee 
from google.auth import compute_engine, impersonated_credentials
from google.cloud import storage
from dateutil.parser import parse
from config import (
    SERVICE_ACCOUNT,
    TIMECARD,
    CSR
    )


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
def ImageExport(image, description, scale, region, fileFormat, bucket, band):
    fileNamePrefix = band+'/'+description # output tif file name
    
    task = ee.batch.Export.image.toCloudStorage(**{
        'image': image,
        'description': description,
        'scale': scale,
        'region': region,
#        'csr' : CSR,
        'fileFormat': fileFormat,
        'bucket': bucket,
        'fileNamePrefix' : fileNamePrefix,
        'formatOptions': {'cloudOptimized': True}        
    })
    task.start()

# function :
# imageList(in) : list of image collection
def ExportIteration(imageList, scale_in, bucket_in, band_in):

    # get file list from bucket to avoid fetching existed image.
    dirList = []
    bucket = storage_client.bucket(bucket_in)
    blobs  = storage_client.list_blobs(bucket)
    for blob in blobs:
        dirList.append(blob.name)

    for ii in range(imageList.size().getInfo()):
        image          = ee.Image(imageList.get(ii))
        image_in       = image.reproject(crs='EPSG:4326',scale=10)
        description_in = image.get('system:index').getInfo()
        region_in      = region.getInfo()['coordinates']
        fileformat_in  = 'GeoTIFF'

        filename = band_in + '/' +description_in + '.tif'
        
        # get image that has not fetched.
        if filename in dirList:
            print(ii, description_in, 'already exists.')
        else:
            ImageExport(image_in, description_in, scale_in, region_in, fileformat_in, bucket_in, band_in)
            print(ii, description_in, 'was created.')
            
    print('finish:', bucket_in)


def bucket_exisitence_comfirmation(storage_client_in, bucket_name_in):
    gcs_buckets = storage_client_in.list_buckets()
    gcs_bucket_list = []
    for blob in gcs_buckets:
        gcs_bucket_list.append(blob.name)

    if bucket_name_in in gcs_bucket_list:
        print(bucket_name_in, 'already exists.')
    else:
        bucket = storage_client_in.create_bucket(bucket_name_in)
        print('newly created', bucket_name_in)

def directory_existense_confirmation(storage_client_in, bucket_name_in, band_in):
    file_name = '../Const/' + TIMECARD 
    destination_blob_name = band_in + '/' + TIMECARD    
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_name)

    
# main processing
if __name__ == '__main__':
    # get arguments
    args = sys.argv
    if 5 <= len(args):
        BAND  = args[1]
        SCALE = int(args[2])
        SDATE = args[3]
        EDATE = args[4]
        print(BAND, SCALE, SDATE, EDATE)
    else:
        print('too few arguments.')
        print('usage')
        print('$pyrhon S2ImageDownloader.py [arg1] [arg2] [arg3] [arg4]')
        print('  arg1: BAND : ex)B8A')
        print('  arg2: scale: ex)10')
        print('  arg3: SDATE: ex)2022-01-01')
        print('  arg4: EDATE: ex)2022-12-31')
        quit()


    # create timecard
    f = open('../Const/'+ TIMECARD, 'w')   
    dt_now = datetime.datetime.now()
    f.write(str(dt_now)+'\n')
    
    # processing for credential
    credentials    = ee.ServiceAccountCredentials( SERVICE_ACCOUNT, '.private-key.json')
    storage_client = storage.Client.from_service_account_json('.private-key.json')
    ee.Initialize(credentials)

    # AOI definition
    region=ee.Geometry.Rectangle([130.387545,33.012406, 130.497408,32.898326])
        
    # get image cpllection
    S2_Image  = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(region).filterDate(parse(SDATE),parse(EDATE)).map(cloudMasking).select([BAND])
    ImageList = S2_Image.toList(300)
        
    # comfirm bucket existense
    bucket_name = 'musi_sentinel2_imagery'
    bucket_exisitence_comfirmation(storage_client, bucket_name)
        
    # comfirm directory exisitense
    directory_existense_confirmation(storage_client, bucket_name, BAND)
        
    # image creation
    ExportIteration(ImageList, SCALE, bucket_name, BAND)
        
    # end processing
    print('Program sucessfully finished.')

        
