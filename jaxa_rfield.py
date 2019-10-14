from datetime import datetime, timedelta
import os
from urllib.request import urlopen
import zipfile
import pandas as pd


def format_jaxa_df(df,
                   d03_grid={'lon_min': 79.521461, 'lon_max': 82.189919, 'lat_min': 5.722969, 'lat_max': 10.064255}):
    df.drop('  Gauge-calibratedRain', axis=1, inplace=True)
    df.rename(columns={' Lat': 'Lat', '  Lon': 'Lon', '  RainRate': 'RainRate'}, inplace=True)
    d03_df = df[
        (df['Lon'] >= d03_grid['lon_min']) & (df['Lon'] <= d03_grid['lon_max']) & (df['Lat'] >= d03_grid['lat_min']) & (
                df['Lat'] <= d03_grid['lat_max'])]
    d03_df = d03_df.reset_index(drop=True)
    return d03_df


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


def create_sat_rfield(jaxa_date, dir_path, time_gap=59):
    time1 = datetime.strptime(jaxa_date, '%Y-%m-%d %H:%M:%S')
    rfield_date = datetime.strptime(jaxa_date, '%Y-%m-%d %H:%M:%S')
    rfield_date = rfield_date.strftime('%Y-%m-%d_%H-%M')
    time2 = time1 + timedelta(minutes=time_gap)
    rfiled_file_name = 'jaxa_{}.txt'.format(rfield_date)
    jaxa_url = get_jaxa_download_url(time1, time2)
    jaxa_zip_file = os.path.join(dir_path, os.path.basename(jaxa_url))
    rfiled_file_path = os.path.join(dir_path, rfiled_file_name)
    try:
        download_file(jaxa_url, jaxa_zip_file)
        downloaded = os.path.exists(jaxa_zip_file) and os.path.isfile(jaxa_zip_file) and os.stat(
            jaxa_zip_file).st_size != 0
        if downloaded:
            unzip_file(jaxa_zip_file, dir_path)
            jaxa_csv_file = os.path.join(dir_path, (os.path.basename(jaxa_url)).replace('.zip', ''))
            df = pd.read_csv(jaxa_csv_file)
            d03_df = format_jaxa_df(df)
            d03_df.to_csv(rfiled_file_path, columns=['RainRate'], header=False, index=None)
            os.remove(jaxa_zip_file)
            os.remove(jaxa_csv_file)
            print('jaxa process completed.')
        else:
            print('jaxa data not available yet for time : '.format(jaxa_date))
    except Exception as e:
        print('create_sat_rfield|Exception :', str(e))


def roundTime(dt=None, dateDelta=timedelta(minutes=1)):
    """Round a datetime object to a multiple of a timedelta
    dt : datetime.datetime object, default now.
    dateDelta : timedelta object, we round to a multiple of this, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
            Stijn Nevens 2014 - Changed to use only datetime objects as variables
    """
    roundTo = dateDelta.total_seconds()
    if dt == None: dt = datetime.now()
    seconds = (dt - dt.min).seconds
    # // is a floor division, not a comment on following line:
    rounding = (seconds + roundTo / 2) // roundTo * roundTo
    return dt + timedelta(0, rounding - seconds, -dt.microsecond)


def gen_rfield():
    dir_path = '/mnt/disks/wrf_nfs/wrf/jaxa/rfield'
    jaxa_date = (roundTime(datetime.now()- timedelta(hours=3), timedelta(minutes=30))).strftime('%Y-%m-%d %H:%M:%S')
    print('Create rfield for {}'.format(jaxa_date))
    create_sat_rfield(jaxa_date, dir_path)


def gen_rain_field(start_time, end_time, dir_path):
    start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    print('start_time : ', start_time)
    print('end_time : ', end_time)
    while start_time <= end_time:
        create_sat_rfield(start_time.strftime('%Y-%m-%d %H:%M:%S'), dir_path, time_gap=59)
        start_time = start_time + timedelta(minutes=30)
    print('png creation completed.')
    print('dir_path : ', dir_path)

gen_rfield()

