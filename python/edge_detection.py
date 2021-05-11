import rasterio
import rasterio.mask
import numpy as np
# import matplotlib.pyplot as plt
from skimage import feature
from skimage.morphology import skeletonize
from shapely.geometry import shape
from shapely.ops import transform
import fiona
import json
import pyproj


wgs84 = pyproj.CRS('EPSG:4326')
utm = pyproj.CRS('EPSG:32724')
utm2wgs84 = pyproj.Transformer.from_crs(utm,wgs84, always_xy=True).transform
# wgs2utm = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform

with fiona.open('/home/delgado/proj/manuscript/data/wm_utm_manuscript.gpkg','r') as wm:
    refgeoms = dict()
    for wm_feat in wm:
        utm_shape=shape(wm_feat['geometry'])
        refgeoms[int(wm_feat['properties']['id_jrc'])] = utm_shape

# f='/home/delgado/proj/manuscript/data/S1A_IW_GRDH_1SDV_20191002T081713_20191002T081738_029277_0353A5_9486_4348.tif'
f='/home/delgado/proj/manuscript/data/S1A_IW_GRDH_1SDV_20191002T081713_20191002T081738_029277_0353A5_9486_4350.tif'
# f='/home/delgado/proj/manuscript/data/S1A_IW_GRDH_1SDV_20191002T081713_20191002T081738_029277_0353A5_9486_4501.tif'
# f='/home/delgado/proj/manuscript/data/S1A_IW_GRDH_1SDV_20191002T081713_20191002T081738_029277_0353A5_9486_4600.tif'

id = edge_classification(f)
shp=refgeoms[int(id)]

skeleton, out_transform = morphological_transformations(f,shp,utm2wgs84)


save_edge_coordinates(skeleton,f,out_transform)

# plt.imshow(skeleton)

def edge_classification(tif_filename):

    # open radar data after speckle filtering and geometric correction etc (see buhayra)
    with rasterio.open(tif_filename,'r') as ds:
        im=ds.read(1)

    # standardize data ("feature scaling", "z-score normalization")
    im=(im-np.mean(im))/np.std(im)

    # plt.imshow(im)

    # apply canny edge detection with very conservative low and high threshold
    edges1 = feature.canny(im,sigma=2,low_threshold=0.8,high_threshold=1)
    # plt.imshow(edges1)

    # Open metadata (affine parameters) and save projected edges
    with open(tif_filename[:-3]+'json', 'r') as fjson:
        metadata = json.load(fjson)

    affParam=rasterio.Affine.from_gdal(metadata[0],metadata[1],metadata[2],metadata[3],metadata[4],metadata[5])
    projected_edges = rasterio.open(tif_filename[:-4] + '_projected_edges.tif', 'w', driver='GTiff',
                                height = edges1.shape[0], width = edges1.shape[1],
                                count=1, dtype=edges1.astype(rasterio.int16).dtype,
                                crs='+proj=latlong',
                                transform=affParam)
    projected_edges.write(edges1.astype(rasterio.int16),1)
    projected_edges.close()
    id=int(tif_filename[:-4].split('_')[9])
    return id


# refgeom is a shapely polygon. crs_transform is of class pyproj.Transformer.from_crs
def morphological_transformations(tif_filename,refgeom,crs_transform):
    id=tif_filename[:-4].split('_')[9]

    # Buffer/dilate maximum extent of reservoir polygon for masking by 0.5*sqrt(A/pi).
    # Reproject in UTM.
    wgs_shape = transform(crs_transform, refgeom.buffer(0.5*(refgeom.area/3.14)**0.5))

    # Mask edge raster with dilated shape
    with rasterio.open(tif_filename[:-4] + '_projected_edges.tif' ) as src:
        out_image, out_transform = rasterio.mask.mask(src, [wgs_shape], crop=True)
        out_meta = src.meta

    ## Morphlogical Transformations to the edge raster: create kernel, dilate edges, skeletonize
    ## kernel is a circle of diameter 3
    ## dilate edges to bridge spurious discontinuities in edge
    ## skeletonize to restore linear edges

    import cv2
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
    dilated = cv2.dilate(out_image[0],kernel)
    skeleton = skeletonize(dilated).astype(rasterio.int16)
    return skeleton, out_transform




    # plt.imshow(dilated)
    # plt.imshow(skeleton)


def save_edge_coordinates(skeleton,tif_filename,out_transform):
    ## Obtain coordinates of each raster cell that was classified as an edge

    pts=list()
    polys=list()
    snake_i=0
    for pol, value in rasterio.features.shapes(skeleton, connectivity=8, transform=out_transform):
        if value == 1:
            polys.append(rasterio.features.rasterize((pol,1),
                fill=0,
                all_touched=True,
                out=np.zeros(skeleton.shape),
                transform=out_transform))
            ij=np.where(1 == rasterio.features.rasterize((pol,1),fill=0,out=np.zeros(skeleton.shape),transform=out_transform))
            if len([ii for ii,jj in zip(*ij)])>=10: # we need at least 4 points to draw a polygon so it is better to have much more points to draw a concave hull around the feature
                for ii,jj in zip(*ij):
                    pts.append([snake_i] + list(rasterio.transform.xy(out_transform,ii,jj)))
            snake_i=snake_i+1

    # Save coordinates as a geospatial dataframe
    import pandas as pd
    import geopandas as gpd

    df = pd.DataFrame({'id':[line[0] for line in pts],'x':[line[1] for line in pts],'y':[line[2] for line in pts]})

    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.x,df.y))

    # Export as geojson
    gdf.to_file(tif_filename[:-3]+'geojson',driver='GeoJSON')

# start R and run
# library(dplyr)
# library(sf)
# library(concaveman)
#
# edges_pts=st_read('../data/edges_points_v1.geojson') %>% st_transform(32724)
# selected_pts = edges_pts %>% group_by(id) %>% tally %>% filter(n==max(n))
# polygon = selected_pts %>% concaveman(.,concavity=1.5)
