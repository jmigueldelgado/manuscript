def query(month):
    rows_list=[]
    for index,id_jrc,ingestion_time,area,geo,max_ingest in cursor:
        data={'id':index,
              'id_jrc':id_jrc,
              'ingestion_time':ingestion_time,
              'area':area,
              'geometry':shapely.wkt.loads(geo),
              'max':max_ingest}
        rows_list.append(data)
    gdf=gpd.GeoDataFrame(rows_list,crs='epsg:4326').set_index(['id'])
    gdf_unique=gdf.loc[gdf['max']==gdf['ingestion_time']].copy()
    return gdf

def burn(gdf, meta):
    gdf['new_column']=0
    all=gdf.dissolve('new_column')
    shapes = ((geom) for id_jrc, geom in zip(gdf.id_jrc, gdf.geometry))
    burned = features.rasterize(shapes=shapes, out_shape=[meta['height'],meta['width']],fill=0, transform=meta['transform'])
    return burned

def combine_in_xarray(burned_list):
    
    return burned_xarray