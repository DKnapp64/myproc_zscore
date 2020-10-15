import os
from unittest.mock import call, MagicMock, patch

from click.testing import CliRunner
import pytest

from proc_gcs_utils import gcs
from src import app


fake_gcp_project_name = 'bogus-project'
fake_gcs_bucket_name = 'bogus-bucket'
fake_source_path = 'path/to/inputs'
fake_baseline_path = 'path/to/baseline/inputs'
fake_baseline_temp_dir = '/tmp/fake/baseline/temp/dir'
fake_destination_path = 'path/to/outputs'
fake_destination_temp_dir = '/tmp/fake/output/temp/dir'
fake_quad_ids = ['quad_id_0', 'quad_id_1']


def test_main():
    mock_process_folders = MagicMock()
    runner = CliRunner()
    with patch('src.app.process_folders', mock_process_folders):
        result = runner.invoke(app.main, [
            fake_gcp_project_name,
            fake_gcs_bucket_name,
            fake_source_path,
            fake_baseline_path,
            fake_destination_path
        ])

    assert result.exit_code == 0, result.output

    mock_process_folders.assert_called_once_with(fake_gcp_project_name,
                                                 fake_gcs_bucket_name,
                                                 fake_source_path,
                                                 fake_baseline_path,
                                                 fake_destination_path)


class FakeGcsBlob:
    def __init__(self, blob_name):
        self.name = blob_name


class TestProcessFolders:

    def test_happy_path(self):
        fake_gcs_subfolders = fake_quad_ids
        mock_gcs = MagicMock()
        mock_gcs.list_bucket_folders.return_value = fake_gcs_subfolders
        mock_gcs.gcs_join = gcs.gcs_join
        mock_tempfile = MagicMock()
        mock_tempfile.mkdtemp.side_effect = [
            fake_baseline_temp_dir,
            fake_destination_temp_dir
        ]
        mock_process_folder = MagicMock()
        with patch.multiple('src.app',
                            gcs=mock_gcs,
                            process_folder=mock_process_folder,
                            tempfile=mock_tempfile):
            app.process_folders(fake_gcp_project_name,
                                fake_gcs_bucket_name,
                                fake_source_path,
                                fake_baseline_path,
                                fake_destination_path)

        mock_gcs.list_bucket_folders.assert_called_once_with(fake_gcp_project_name,
                                                             fake_gcs_bucket_name,
                                                             fake_source_path)

        mock_gcs.download_files.assert_has_calls([
            call(fake_gcp_project_name,
                 fake_gcs_bucket_name,
                 fake_baseline_path,
                 fake_baseline_temp_dir)
        ])
        mock_process_folder.assert_has_calls([
            call(fake_gcp_project_name,
                 fake_gcs_bucket_name,
                 '{0}/{1}'.format(fake_source_path, fake_gcs_subfolders[0]),
                 fake_baseline_temp_dir,
                 fake_destination_temp_dir),
            call(fake_gcp_project_name,
                 fake_gcs_bucket_name,
                 '{0}/{1}'.format(fake_source_path, fake_gcs_subfolders[1]),
                 fake_baseline_temp_dir,
                 fake_destination_temp_dir)
        ])
        mock_gcs.upload_files.assert_called_once_with(fake_gcp_project_name,
                                                      fake_gcs_bucket_name,
                                                      fake_destination_path,
                                                      fake_destination_temp_dir)

    def test_raises_if_source_folder_is_empty(self):
        mock_gcs = MagicMock()
        mock_gcs.list_bucket_folders.return_value = []
        with patch('src.app.gcs', mock_gcs):
            with pytest.raises(ValueError):
                app.process_folders(fake_gcp_project_name,
                                    fake_gcs_bucket_name,
                                    fake_source_path,
                                    fake_baseline_path,
                                    fake_destination_path)


class TestProcessFolder:

    def test_happy_path(self):
        fake_subfolder_name = fake_quad_ids[0]
        fake_source_temp_dir = '/tmp/fake/source/temp/dir'
        fake_source_subfolder_gcs_path = gcs.gcs_join([fake_source_path, fake_subfolder_name])
        fake_baseline_temp_path = os.path.join(fake_baseline_temp_dir,
                                               '{}_baseline.tif'.format(fake_subfolder_name))
        fake_destination_temp_path = os.path.join(fake_destination_temp_dir,
                                                  '{}_change.tif'.format(fake_subfolder_name))
        mock_gcs = MagicMock()
        mock_os = MagicMock()
        mock_os.listdir.side_effect = [
            ['{}_baseline.tif'.format(quad_id) for quad_id in fake_quad_ids]
        ]
        mock_os.path.join = os.path.join
        mock_tempfile = MagicMock()
        mock_tempfile.mkdtemp.return_value = fake_source_temp_dir
        mock_change = MagicMock()
        with patch.multiple('src.app',
                            change=mock_change,
                            gcs=mock_gcs,
                            os=mock_os,
                            tempfile=mock_tempfile):
            app.process_folder(fake_gcp_project_name,
                               fake_gcs_bucket_name,
                               fake_source_subfolder_gcs_path,
                               fake_baseline_temp_dir,
                               fake_destination_temp_dir)

        mock_gcs.download_files.assert_called_once_with(fake_gcp_project_name,
                                                        fake_gcs_bucket_name,
                                                        fake_source_subfolder_gcs_path,
                                                        fake_source_temp_dir)
        mock_change.measure_change.assert_called_once_with(fake_source_temp_dir,
                                                           fake_baseline_temp_path,
                                                           fake_destination_temp_path)

    def test_returns_if_baseline_not_found(self):
        fake_subfolder_name = fake_quad_ids[0]
        fake_source_subfolder_gcs_path = '{0}/{1}'.format(fake_source_path, fake_subfolder_name)
        mock_os = MagicMock()
        mock_os.listdir.return_value = ['not_the_quad_youre_looking_for.tif']
        mock_os.path.join = os.path.join
        with patch('src.app.os', mock_os):
            app.process_folder(fake_gcp_project_name,
                               fake_gcs_bucket_name,
                               fake_source_subfolder_gcs_path,
                               fake_baseline_temp_dir,
                               fake_destination_temp_dir)
