import os
import logging
import tempfile

import click
from proc_gcs_utils import gcs

from src import change_zscore


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')


def process_folder(gcp_project_name,
                   gcs_bucket_name,
                   source_subfolder_gcs_path,
                   baseline_quad_temp_dir,
                   destination_temp_dir):

    quad_id = source_subfolder_gcs_path.split('/')[-1]

    try:
        baseline_quad_file_name = [f for f in os.listdir(baseline_quad_temp_dir) if quad_id in f][0]
    except IndexError:
        logging.warning('No baseline found for quad {}'.format(quad_id))
        return
    baseline_quad_path = os.path.join(baseline_quad_temp_dir, baseline_quad_file_name)

    source_quad_temp_dir = tempfile.mkdtemp()
    gcs.download_files(gcp_project_name,
                       gcs_bucket_name,
                       source_subfolder_gcs_path,
                       source_quad_temp_dir)

    destination_quad_name = '{}_zscore.tif'.format(quad_id)
    destination_quad_path = os.path.join(destination_temp_dir,
                                         destination_quad_name)
    change_zscore.measure_change(source_quad_temp_dir,
                          baseline_quad_path,
                          destination_quad_path)


def process_folders(gcp_project_name,
                    gcs_bucket_name,
                    source_gcs_path,
                    baseline_gcs_path,
                    destination_gcs_path):
    source_gcs_folders = gcs.list_bucket_folders(gcp_project_name,
                                                 gcs_bucket_name,
                                                 source_gcs_path)
    if not source_gcs_folders:
        raise ValueError('No subfolders found in {}'.format(source_gcs_path))
    else:
        logging.info('Found {} sets of quads to evaluate'.format(len(source_gcs_folders)))

    baseline_quad_temp_dir = tempfile.mkdtemp()
    logging.info('Downloading baseline quads from GCS')
    gcs.download_files(gcp_project_name,
                       gcs_bucket_name,
                       baseline_gcs_path,
                       baseline_quad_temp_dir)

    destination_quad_temp_dir = tempfile.mkdtemp()
    for f in source_gcs_folders:
        logging.info('Evaluating samples in {}'.format(f))
        process_folder(gcp_project_name,
                       gcs_bucket_name,
                       gcs.gcs_join([source_gcs_path, f]),
                       baseline_quad_temp_dir,
                       destination_quad_temp_dir)

    logging.info('Uploading results to GCS')
    gcs.upload_files(gcp_project_name,
                     gcs_bucket_name,
                     destination_gcs_path,
                     destination_quad_temp_dir)


@click.command()
@click.argument('gcp_project_name')
@click.argument('gcs_bucket_name')
@click.argument('source_path')
@click.argument('baseline_path')
@click.argument('destination_path')
def main(gcp_project_name,
         gcs_bucket_name,
         source_path,
         baseline_path,
         destination_path):

    process_folders(gcp_project_name,
                    gcs_bucket_name,
                    source_path,
                    baseline_path,
                    destination_path)


if __name__ == '__main__':
    main()
