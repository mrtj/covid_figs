import os
import json
import logging
import tempfile

import boto3

from dataset import DataSet
from ts_viz import TimeSeriesViz, OverviewViz

logger = logging.getLogger()

def upload_file(local_name, file_name, public=False):
    s3_client = boto3.client('s3')
    bucket_name = os.environ['NSP_S3_BUCKET_NAME']
    prefix = os.environ['NSP_S3_PREFIX']
    remote_name = os.path.join(prefix, file_name)
    print(f'*** Uploading {local_name} -> s3://{bucket_name}/{remote_name}')
    ea = {'ACL': 'public-read'} if public else None
    s3_client.upload_file(local_name, bucket_name, remote_name, ExtraArgs=ea)
    return (bucket_name, remote_name)

def handler(event, context):
    print('request started')
    
    regional_ds = DataSet('dati-regioni/dpc-covid19-ita-regioni.csv')
    print(regional_ds)

    national_ds = DataSet('dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv', resample=True)
    print(national_ds)
    
    with tempfile.TemporaryDirectory() as tmpdirname:
    
        lombardia_df = regional_ds.df[regional_ds.df['denominazione_regione'] == 'Lombardia']
        lombardia_overview_viz = OverviewViz('Lombardia', lombardia_df, regional_ds.last_modified, fig_folder=tmpdirname)
        _, lombardia_last = lombardia_overview_viz.show_overview(save_fig=True)

        italia_df = national_ds.df
        italia_overview_viz = OverviewViz('Italia', italia_df, national_ds.last_modified, fig_folder=tmpdirname)
        _, italia_last = italia_overview_viz.show_overview(save_fig=True)
        
        bucket, last = upload_file(lombardia_last, 'lombardia-overview.png', public=True)
        lombardia_last_remote = f's3://{bucket}/{last}'
        bucket, last = upload_file(italia_last, 'italia-overview.png', public=True)
        italia_last_remote = f's3://{bucket}/{last}'
    
    return {
        'lombardia': {
            'url': lombardia_last_remote,
            'last_modified': regional_ds.last_modified.replace(microsecond=0).astimezone().isoformat()
        },
        'italia': {
            'url': italia_last_remote,
            'last_modified': national_ds.last_modified.replace(microsecond=0).astimezone().isoformat()
        }
    }
