from datetime import datetime, timedelta
import os
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
import glob
import zipfile

import imageio
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg


def format_jaxa_df(df,
                   d03_grid={'lon_min': 79.521461, 'lon_max': 82.189919, 'lat_min': 5.722969, 'lat_max': 10.064255}):
    df.drop('  Gauge-calibratedRain', axis=1, inplace=True)
    df.rename(columns={' Lat': 'Lat', '  Lon': 'Lon', '  RainRate': 'RainRate'}, inplace=True)
    d03_df = df[
        (df['Lon'] >= d03_grid['lon_min']) & (df['Lon'] <= d03_grid['lon_max']) & (df['Lat'] >= d03_grid['lat_min']) & (
                    df['Lat'] <= d03_grid['lat_max'])]
    d03_df = d03_df.reset_index(drop=True)
    return d03_df


def create_png(d03_df,
               output_image_path='/home/hasitha/PycharmProjects/Jaxa/output/output.png',
               base_image_path='/home/hasitha/PycharmProjects/Jaxa/input/map.png',
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


def unzip_file(src, dest='/home/hasitha/PycharmProjects/Jaxa/output'):
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


def list_files(path, ext):
    files = [f for f in glob.glob(path + "**/*.{}".format(ext), recursive=True)]
    return files


def create_gif(filenames, output, duration=0.5):
    images = []
    for filename in filenames:
        images.append(imageio.imread(filename))
    imageio.mimsave(output, images, duration=duration)


def download_jaxa_data_for_given_time_frame(start_time, end_time, time_step=30, time_gap=59,
                                            dir_path='/home/hasitha/PycharmProjects/Jaxa/output'):
    """
    :param start_time: str '2019-10-12 08:00:00'
    :param end_time: str '2019-10-12 18:00:00'
    :param dir_path:
    :return:
    """
    date_dir = datetime.now().strftime('%Y-%m-%d')
    dir_path = os.path.join(dir_path, date_dir)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    gif_time = start_time
    end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    print('start_time : ', start_time)
    print('end_time : ', end_time)
    while start_time <= end_time:
        print('start_time : ', start_time)
        time1 = start_time
        time2 = start_time + timedelta(minutes=time_gap)
        jaxa_url = get_jaxa_download_url(time1, time2)
        jaxa_zip_file = os.path.join(dir_path, os.path.basename(jaxa_url))
        try:
            download_file(jaxa_url, jaxa_zip_file)
            unzip_file(jaxa_zip_file, dir_path)
            jaxa_csv_file = os.path.join(dir_path, (os.path.basename(jaxa_url)).replace('.zip', ''))
            df = pd.read_csv(jaxa_csv_file)
            d03_df = format_jaxa_df(df)
            image_file_name = '{}.png'.format(time1.strftime('%Y-%m-%d_%H:%M:%S'))
            image_file_path = os.path.join(dir_path, image_file_name)
            create_png(d03_df, image_file_path)
            start_time = start_time + timedelta(minutes=time_step)
        except Exception as e:
            print('Exception :', str(e))
    print('png creation completed.')
    print('dir_path : ', dir_path)
    png_list = list_files(dir_path, 'png')
    if len(png_list) > 0:
        gif_file = os.path.join(dir_path, '{}.gif'.format(gif_time.strftime('%Y-%m-%d_%H:%M:%S')))
        create_gif(png_list, gif_file)
        print('GIF creation completed.')


def get_jaxa_download_url(time1, time2):
    jaxa_url = 'ftp://rainmap:Niskur+1404@hokusai.eorc.jaxa.jp/now/txt/05_AsiaSS/' \
               'gsmap_now.{}{}{}.{}{}_{}{}.05_AsiaSS.csv.zip'.format(time1.strftime('%Y'),
                                                                     time1.strftime('%m'),
                                                                     time1.strftime('%d'),
                                                                     time1.strftime('%H'),
                                                                     time1.strftime('%M'),
                                                                     time2.strftime('%H'),
                                                                     time2.strftime('%M'))
    return jaxa_url


if __name__ == '__main__':
    download_jaxa_data_for_given_time_frame('2019-10-13 00:00:00',
                                            '2019-10-13 13:00:00')

