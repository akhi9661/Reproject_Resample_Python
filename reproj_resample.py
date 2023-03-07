'''
This code module reprojects and resamples all images in a folder to a reference image. The code works with both single band as
well as multi-band images.

Inputs:
input_folder = folder containing all the images.
file_ref = Reference image for projection system and resampling.

Output:
Final output folder: 'Resampled'

Note: A temporary image is generated as well but is automatically removed after the process is completed.

'''

input_folder = input("Enter the folder path containing files to be reprojected and resampled:\n")
file_ref = input("Enter the path of the reference image:\n")

''' ------------------------------------------------------------------------------------------------------------------ '''

import os, shutil, rasterio
from osgeo import gdal, osr, gdalconst
import rioxarray as rxr, numpy as np
from rasterio.warp import calculate_default_transform, reproject
from rasterio.enums import Resampling

''' ------------------------------------------------------------------------------------------------------------------ '''

def resample_image(inpf, inp_name, file_ref, opf):
    
    file_inp = os.path.join(inpf, inp_name)
    file_reproj = reproject_raster(file_inp, file_ref, inp_name)
    
    ref = os.path.basename(file_ref)
    
    print(f'Resampling: "{inp_name}" to "{ref}"')
    
    reference = gdal.Open(file_ref, 0)
    referenceTrans = reference.GetGeoTransform()
    x_res = referenceTrans[1]
    y_res = -referenceTrans[5]

    opf_resample = os.path.join(opf, os.path.basename(inp_name).split('.')[0] + '_resample.TIF')

    kwargs = {"format": "GTiff", "xRes": x_res, "yRes": y_res}
    ds = gdal.Warp(opf_resample, file_reproj, **kwargs)
    ds = None
    
    print(f'Done: "{inp_name}"\n')
    return file_reproj

def reproject_raster(file_inp, file_ref, inp_name):
    
    ref = os.path.basename(file_ref)
    
    print(f'Reprojecting: "{inp_name}" to "{ref}"')
    src_rast = rxr.open_rasterio(file_ref, masked=True).squeeze()
    cc = src_rast.rio.crs.to_proj4()
    crs = cc.split('=')[1]
    
    out_path = os.path.join(opf, 'Temp_reproject.TIF')
    
    with rasterio.open(file_inp) as src:
        src_crs = src.crs
        transform, width, height = calculate_default_transform(src_crs, crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        
        kwargs.update({"nodata": np.iinfo(src.dtypes[0]).min})

        kwargs.update({'crs': crs,
                       'transform': transform,
                       'width': width,
                       'height': height})

        with rasterio.open(out_path, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(source = rasterio.band(src, i),
                          destination = rasterio.band(dst, i),
                          src_transform = src.transform,
                          src_crs = src.crs,
                          dst_transform = transform,
                          dst_crs = crs,
                          resampling = Resampling.nearest)
    
    return out_path

opf = os.path.join(input_folder, 'Resampled')
if os.path.exists(opf):
    shutil.rmtree(opf)
os.makedirs(opf)

original = os.listdir(input_folder)
gtif = list(filter(lambda x: x.endswith(("tif", "TIF", "img")), original))
for gi in gtif:
    temp_proj = resample_image(input_folder, gi, file_ref, opf)
    
os.remove(temp_proj)
