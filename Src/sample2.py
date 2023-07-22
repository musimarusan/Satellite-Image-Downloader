import ee

ee.Initialize()
region=ee.Geometry.Rectangle([104.75,13.40,105.25,12.90]);

def cloudMasking(image):
    qa = image.select('QA60')
    cloudBitMask = 1 << 10 #cloudShadowBitMask = ee.Number(2).pow(3).int();  
    cirrusBitMask = 1 << 11 #cloudsBitMask = ee.Number(2).pow(5).int();
    # Both flags should be set to zero, indicating clear conditions.
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
    return image.updateMask(mask).divide(10000)

def ImageExport(image,description,folder,region,scale):
    task = ee.batch.Export.image.toDrive(image=image,description=description,folder=folder,region=region,scale=scale)
    task.start()

def FeatureExport(collection,description,folder,fileFormat):
    task = ee.batch.Export.table.toDrive(collection=collection,description=description,folder=folder,fileFormat=fileFormat)
    task.start()

for i in ["20181217T032129_20181217T033234_T48PWV","20181217T032129_20181217T033234_T48PVV"]:
    print('COPERNICUS/S2/'+i)
    forimage = cloudMasking(ee.Image('COPERNICUS/S2/'+i)).select(['B2','B3','B4','B8','B11','B12'])
    formeta = ee.Image('COPERNICUS/S2/'+i)
    features = [\
    ee.Feature(None, {'value': formeta.get('SENSING_ORBIT_DIRECTION'),'name':'SENSING_ORBIT_DIRECTION'}),\
    ee.Feature(None, {'value': formeta.get('GENERATION_TIME'),'name':'GENERATION_TIME'}),\
    ee.Feature(None, {'value': formeta.get('quality_check'),'name':'quality_check'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_SOLAR_AZIMUTH_ANGLE'),'name':'MEAN_SOLAR_AZIMUTH_ANGLE'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_SOLAR_ZENITH_ANGLE'),'name':'MEAN_SOLAR_ZENITH_ANGLE'}),\
    ee.Feature(None, {'value': formeta.get('SOLAR_IRRADIANCE_B2'),'name':'SOLAR_IRRADIANCE_B2'}),\
    ee.Feature(None, {'value': formeta.get('SOLAR_IRRADIANCE_B3'),'name':'SOLAR_IRRADIANCE_B3'}),\
    ee.Feature(None, {'value': formeta.get('SOLAR_IRRADIANCE_B4'),'name':'SOLAR_IRRADIANCE_B4'}),\
    ee.Feature(None, {'value': formeta.get('SOLAR_IRRADIANCE_B8'),'name':'SOLAR_IRRADIANCE_B8'}),\
    ee.Feature(None, {'value': formeta.get('SOLAR_IRRADIANCE_B11'),'name':'SOLAR_IRRADIANCE_B11'}),\
    ee.Feature(None, {'value': formeta.get('SOLAR_IRRADIANCE_B12'),'name':'SOLAR_IRRADIANCE_B12'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_INCIDENCE_AZIMUTH_ANGLE_B2'),'name':'MEAN_INCIDENCE_AZIMUTH_ANGLE_B2'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_INCIDENCE_AZIMUTH_ANGLE_B3'),'name':'MEAN_INCIDENCE_AZIMUTH_ANGLE_B3'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_INCIDENCE_AZIMUTH_ANGLE_B4'),'name':'MEAN_INCIDENCE_AZIMUTH_ANGLE_B4'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_INCIDENCE_AZIMUTH_ANGLE_B8'),'name':'MEAN_INCIDENCE_AZIMUTH_ANGLE_B8'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_INCIDENCE_AZIMUTH_ANGLE_B11'),'name':'MEAN_INCIDENCE_AZIMUTH_ANGLE_B11'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_INCIDENCE_AZIMUTH_ANGLE_B12'),'name':'MEAN_INCIDENCE_AZIMUTH_ANGLE_B12'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_INCIDENCE_ZENITH_ANGLE_B2'),'name':'MEAN_INCIDENCE_ZENITH_ANGLE_B2'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_INCIDENCE_ZENITH_ANGLE_B3'),'name':'MEAN_INCIDENCE_ZENITH_ANGLE_B3'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_INCIDENCE_ZENITH_ANGLE_B4'),'name':'MEAN_INCIDENCE_ZENITH_ANGLE_B4'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_INCIDENCE_ZENITH_ANGLE_B8'),'name':'MEAN_INCIDENCE_ZENITH_ANGLE_B8'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_INCIDENCE_ZENITH_ANGLE_B11'),'name':'MEAN_INCIDENCE_ZENITH_ANGLE_B11'}),\
    ee.Feature(None, {'value': formeta.get('MEAN_INCIDENCE_ZENITH_ANGLE_B12'),'name':'MEAN_INCIDENCE_ZENITH_ANGLE_B12'})\
    ]
    metadata = ee.FeatureCollection(features);
    ImageExport(forimage.reproject(crs='EPSG:4326',scale=10),i,'Cambodia',region['coordinates'][0],10)
    FeatureExport(metadata,i,'Cambodia','CSV')

    
