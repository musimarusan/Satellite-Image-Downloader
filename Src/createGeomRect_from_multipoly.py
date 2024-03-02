import numpy as np
import geopandas as gpd


def check_crs(gdf):
    if gdf.crs is None:
        return False
    if gdf.crs.name == 'Undefined geographic SRS':
        return False
    return True


polygon = './Boundary_Nagasu-town.gpkg'

#polygon = '/home/hiroakit/Research/devel/Satellite-Image-Downloader/Data/raw/Poly/Boundary_Giza_Pyramid.gpkg'

gdf = gpd.read_file(polygon)

assert check_crs(gdf), 'CRS os not defined.'



s = str(gdf['geometry'][0])
print(s)
quit()

s = s.replace('MULTIPOLYGON ','')
s = s.replace('(((',' ')
s = s.replace(')))','')

lonlat = s.split(',')
print(len(lonlat))
#print(lonlat[0])

nplonlat = np.array(lonlat)
#print(nplonlat[10])

lon = []
lat = []
for coord in lonlat:
#    print(coord)
    tmpcoord = coord.split(' ')
#    print(tmpcoord)
    lon.append(tmpcoord[1])
    lat.append(tmpcoord[2])


print(min(lon),max(lat))
print(max(lon),min(lat))

