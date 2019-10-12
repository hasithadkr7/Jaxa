from datetime import datetime
import os
from urllib.request import urlopen
import glob
import zipfile
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg


def format_jaxa_df(df,
                   d03_grid={'lon_min': 79.521461, 'lon_max': 82.189919, 'lat_min': 5.722969, 'lat_max': 10.064255}):
    d03_df = df[
        (df['Lon'] >= d03_grid['lon_min']) & (df['Lon'] <= d03_grid['lon_max']) & (df['Lat'] >= d03_grid['lat_min']) & (
                    df['Lat'] <= d03_grid['lat_max'])]
    d03_df = d03_df.reset_index(drop=True)
    return d03_df


def create_png(d03_df,
               base_image_path='/home/hasitha/PycharmProjects/DSS-Framework/jupyter_notebooks/jaxa_data/map.png',
               output_image_path='/home/hasitha/PycharmProjects/DSS-Framework/jupyter_notebooks/jaxa_data/output.png',
               image_extent=[79.55, 82.15, 5.75, 10.05]):
    lanka_img = mpimg.imread(base_image_path)
    ax = d03_df.plot(kind="scatter", x="Lon", y="Lat", figsize=(12, 10),
                     label="RainRate", c="RainRate", cmap=plt.get_cmap("jet"),
                     colorbar=False, alpha=0.5)
    plt.imshow(lanka_img, extent=image_extent, alpha=0.4)
    plt.ylabel("", fontsize=14)
    plt.xlabel("", fontsize=14)
    plt.tick_params(colors='w')

    cbar = plt.colorbar()
    cbar.set_cmap("jet")
    cbar.solids.set_edgecolor("face")
    cbar.solids.set_cmap("jet")
    cbar.set_label('RainRate', fontsize=16, alpha=1,
                   rotation=270, labelpad=20)
    plt.legend(fontsize=16)
    plt.savefig(output_image_path)


def unzip_file(src, dest='/home/hasitha/PycharmProjects/DSS-Framework/jupyter_notebooks/jaxa_data'):
    with zipfile.ZipFile(src, 'r') as zip_ref:
        zip_ref.extractall(dest)


def download_file(url, dest):
    f = urlopen(url)
    with open(dest, "wb") as local_file:
        local_file.write(f.read())


def download_jaxa_data(date_str, dir_path=None):
    data_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    login = 'rainmap:Niskur+1404'
    jaxa_url = 'ftp://' + login + '@hokusai.eorc.jaxa.jp/now/txt/05_AsiaSS/gsmap_now.YYYYMMDD.HH00_HH59.05_AsiaSS.csv.zip'
    date_dic = {'YYYY': data_date.strftime('%Y'), 'MM': data_date.strftime('%m'), 'DD': data_date.strftime('%d'),
                'HH': data_date.strftime('%H')}
    for k, v in list(date_dic.items()):
        jaxa_url = jaxa_url.replace(k, v)
    if dir_path is not None:
        data_path = os.path.join(dir_path, 'jaxa_data')
    else:
        data_path = os.path.join(os.getcwd(), 'jaxa_data')
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    jaxa_zip_file = os.path.join(data_path, os.path.basename(jaxa_url))
    download_file(jaxa_url, jaxa_zip_file)
    return jaxa_zip_file


