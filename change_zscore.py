import logging
import os

from osgeo import gdal
import numpy as np


def _measure_zscore_change(samples, baseline):
    if samples.shape[-1] < 2:
        logging.warning('Fewer than 2 samples found - skipping')
        return

    is_above_baseline = (samples > baseline[:, :, None])
    count_above_baseline = np.sum(is_above_baseline.astype(np.int), axis=2)

    return count_above_baseline


def _save_output(output_array,
                 output_projection,
                 output_transform,
                 output_file_path):
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ysize, xsize = output_array.shape
    outDataset = driver.Create(output_file_path,
                               xsize=xsize,
                               ysize=ysize,
                               bands=1,
                               eType=gdal.GDT_Int16,
                               options=['BIGTIFF=YES', 'COMPRESS=LZW', 'TILED=YES'])
    outDataset.SetProjection(output_projection)
    outDataset.SetGeoTransform(output_transform)
    outDataset.GetRasterBand(1).WriteArray(output_array)

    del outDataset


def measure_zscore_change(source_quad_dir: str,
                   baseline_quad_path: str,
                   destination_quad_path: str) -> None:
    '''Measure change in samples from a baseline

    Args:
      source_quad_dir - Local path to sample GeoTIFF quads directory
      baseline_quad_path - Local path to baseline GeoTIFF quad file
      destination_quad_path - Local path where output GeoTIFF should be placed
    '''
    full_input_file_paths = [os.path.join(source_quad_dir, f) for f in os.listdir(source_quad_dir)]
    sample_datasets = [gdal.Open(f, gdal.GA_ReadOnly) for f in full_input_file_paths]
    sample_arrays = [ds.GetRasterBand(1).ReadAsArray() for ds in sample_datasets]
    sample_array_3d = np.stack(sample_arrays, axis=2)

    baseline_dataset = gdal.Open(baseline_quad_path, gdal.GA_ReadOnly)
    baseline_array = baseline_dataset.GetRasterBand(1).ReadAsArray()

    measurement = _measure_zscore_change(sample_array_3d, baseline_array)

    if measurement is not None:
        _save_output(measurement,
                     sample_datasets[0].GetProjection(),
                     sample_datasets[0].GetGeoTransform(),
                     destination_quad_path)
