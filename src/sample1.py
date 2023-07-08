import ee
from dateutil.parser import parse
ee.Initialize()
region=ee.Geometry.Rectangle([130.435266,32.942276,130.497408,32.898326])

def cloudMasking(image):
    qa = image.select('QA60')
    cloudBitMask = 1 << 10  
    cirrusBitMask = 1 << 11
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
    return image.updateMask(mask).divide(10000)

def ImageExport(image,description,folder,region,scale):
    task = ee.batch.Export.image.toDrive(image=image,description=description,folder=folder,region=region,scale=scale)
    task.start()

print("--1--")
Sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(region).filterDate(parse('2022-01-01'),parse('2022-12-31')).map(cloudMasking).select(['B8'])
print("--2--")
imageList = Sentinel2.toList(300)
print("--3--") 
for i in range(imageList.size().getInfo()):
    print(i)
    image = ee.Image(imageList.get(i))
    ImageExport(image.reproject(crs='EPSG:4326',scale=10),image.get('system:index').getInfo(),'S2_MS',region['coordinates'][0],10)

