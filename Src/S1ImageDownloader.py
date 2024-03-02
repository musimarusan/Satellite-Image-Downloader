# [References]
# https://sites.google.com/site/mizuochipublic/実践コンテンツ/google-earth-engine入門/6-pythonによるローカルからのgee実行?authuser=0
# https://colab.research.google.com/github/csaybar/EEwPython/blob/dev/10_Export.ipynb

import sys
import os
import datetime
import numpy as np
import pandas as pd
import geopandas as gpd
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


#
def check_crs(gdf):
    if gdf.crs is None:
        return False
    if gdf.crs.name == 'Undefined geographic SRS':
        return False
    return True


# get geometry from MULTIPOLYGON
def get_geom_rect(polytype, polygon_in):

    # open and check polygon
    gdf = gpd.read_file(polygon_in)
    assert check_crs(gdf), 'CRS os not defined.'

    # extract polygon
    s = str(gdf['geometry'][0])
    
    if polytype == 'MULTI':    
        s = s.replace('MULTIPOLYGON ','')
        s = s.replace('(((',' ')
        s = s.replace(')))','')
    elif polytype == 'MONO':
        s = str(gdf['geometry'][0])
        s = s.replace('POLYGON ','')
        s = s.replace('((',' ')
        s = s.replace('))','')

    lonlat = s.split(',')        
        
    nplonlat = np.array(lonlat)
    lon = []
    lat = []
    for coord in lonlat:
        tmpcoord = coord.split(' ')
        lon.append(tmpcoord[1])
        lat.append(tmpcoord[2])

    minLon = float(min(lon))
    maxLat = float(max(lat))
    maxLon = float(max(lon))
    minLat = float(min(lat))
    
    return minLon, maxLat, maxLon, minLat


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
    fileNamePrefix = band+'/'+description +'_' + band  # output tif file name
    
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

    # ImageCollection loop
    for ii in range(imageList.size().getInfo()):
        image          = ee.Image(imageList.get(ii))
        image_in       = image.reproject(crs='EPSG:4326',scale=10)
        description_in = image.get('system:index').getInfo()
        region_in      = region.getInfo()['coordinates']
        fileformat_in  = 'GeoTIFF'

        filename = band_in + '/' +description_in + '_' + band_in + '.tif' # target file name. not used for file output
        
        # get image that has not fetched.
        if filename in dirList:
            print(ii, filename, 'already exists.')
        else:
            ImageExport(image_in, description_in, scale_in, region_in, fileformat_in, bucket_in, band_in)
            print(ii, filename, 'as queued.')
            
    print('finish:', bucket_in)


#
def bucket_exisitence_comfirmation(storage_client_in, bucket_name_in):
    gcs_buckets = storage_client_in.list_buckets()
    gcs_bucket_list = []
    for blob in gcs_buckets:
        gcs_bucket_list.append(blob.name)

    if bucket_name_in in gcs_bucket_list:
        print('Bucket ', bucket_name_in, 'is already exists.')
    else:
        bucket = storage_client_in.create_bucket(bucket_name_in)
        print('newly created ', bucket_name_in)

#        
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
        POLY  = args[1] 
        BAND  = args[2]
        SCALE = int(args[3])
        SDATE = args[4]
        EDATE = args[5]
        print(POLY, BAND, SCALE, SDATE, EDATE)
    else:
        print('too few arguments.')
        print('usage')
        print('$pyrhon S1ImageDownloader.py [arg1] [arg2] [arg3] [arg4]')
        print('  arg1: POLY : ex)./')
        print('  arg2: BAND : ex)VV')
        print('  arg3: scale: ex)10')
        print('  arg4: SDATE: ex)2022-01-01')
        print('  arg5: EDATE: ex)2022-12-31')
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
    POLYTYPE = 'MONO'
#    POLYTYPE = 'MULTI'
    min_lon, max_lat, max_lon, min_lat = get_geom_rect(POLYTYPE, POLY)
    print(min_lon, max_lat, max_lon, min_lat)    
    region=ee.Geometry.Rectangle([min_lon, max_lat, max_lon, min_lat])


    # get image cpllection
    S1_Image  = ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(region).filterDate(parse(SDATE),parse(EDATE)).select([BAND])
    ImageList = S1_Image.toList(300)
        
    # comfirm bucket existense
    bucket_name = 'musi_sentinel1_imagery'
    bucket_exisitence_comfirmation(storage_client, bucket_name)
        
    # comfirm directory exisitense
    directory_existense_confirmation(storage_client, bucket_name, BAND)
        
    # image creation
    ExportIteration(ImageList, SCALE, bucket_name, BAND)
        
    # end processing
    print('Program sucessfully finished.')

        
