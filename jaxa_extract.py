import argparse
import ast
import datetime as dt
import logging
import multiprocessing
import os
import shutil
import tempfile
import zipfile
from random import random
import math
import matplotlib
import numpy as np
from curw.rainfall.wrf.extraction import utils as ext_utils
from joblib import Parallel, delayed
from mpl_toolkits.basemap import cm, Basemap
from curw.rainfall.wrf import utils
from curwmysqladapter import Station

matplotlib.use('Agg')
from matplotlib import colors, pyplot as plt


def create_asc_file(data, lats, lons, out_file_path, cell_size=0.1, no_data_val=-99, overwrite=False):
    if not utils.file_exists_nonempty(out_file_path) or overwrite:
        with open(out_file_path, 'wb') as out_file:
            out_file.write(('NCOLS %d\n' % len(lons)).encode())
            out_file.write(('NROWS %d\n' % len(lats)).encode())
            out_file.write(('XLLCORNER %f\n' % lons[0]).encode())
            out_file.write(('YLLCORNER %f\n' % lats[0]).encode())
            out_file.write(('CELLSIZE %f\n' % cell_size).encode())
            out_file.write(('NODATA_VALUE %d\n' % no_data_val).encode())

            np.savetxt(out_file, data, fmt='%.4f')
    else:
        logging.info('%s already exits' % out_file_path)


def create_contour_plot(data, out_file_path, lat_min, lon_min, lat_max, lon_max, plot_title, basemap=None, clevs=None,
                        cmap=plt.get_cmap('Reds'), overwrite=False, norm=None, additional_changes=None, **kwargs):
    """
    create a contour plot using basemap
    :param additional_changes:
    :param norm:
    :param title_ops:
    :param cmap: color map
    :param clevs: color levels
    :param basemap: creating basemap takes time, hence you can create it outside and pass it over
    :param plot_title:
    :param data: 2D grid data
    :param out_file_path:
    :param lat_min:
    :param lon_min:
    :param lat_max:
    :param lon_max:
    :param overwrite:
    :return:
    """
    if not utils.file_exists_nonempty(out_file_path) or overwrite:
        fig = plt.figure(figsize=(8.27, 11.69))
        # ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
        if basemap is None:
            basemap = Basemap(projection='merc', llcrnrlon=lon_min, llcrnrlat=lat_min, urcrnrlon=lon_max,
                              urcrnrlat=lat_max,
                              resolution='h')
        basemap.drawcoastlines()
        parallels = np.arange(math.floor(lat_min) - 1, math.ceil(lat_max) + 1, 1)
        basemap.drawparallels(parallels, labels=[1, 0, 0, 0], fontsize=10)
        meridians = np.arange(math.floor(lon_min) - 1, math.ceil(lon_max) + 1, 1)
        basemap.drawmeridians(meridians, labels=[0, 0, 0, 1], fontsize=10)

        ny = data.shape[0]
        nx = data.shape[1]
        lons, lats = basemap.makegrid(nx, ny)

        if clevs is None:
            clevs = np.arange(-1, np.max(data) + 1, 1)

        cs = basemap.contourf(lons, lats, data, clevs, cmap=cmap, latlon=True, norm=norm)

        cbar = basemap.colorbar(cs, location='bottom', pad="5%")
        cbar.set_label('mm')

        if isinstance(plot_title, str):
            plt.title(plot_title)
        elif isinstance(plot_title, dict):
            plt.title(plot_title.pop('label'), **plot_title)

        # make any additional changes to the plot
        if additional_changes is not None:
            additional_changes(plt, data, **kwargs)

        # draw_center_of_mass(data)
        # com = ndimage.measurements.center_of_mass(data)
        # plt.plot(com[1], com[0], 'ro')

        plt.draw()
        plt.savefig(out_file_path)
        plt.close()
    else:
        logging.info('%s already exists' % out_file_path)


def process_jaxa_zip_file(zip_file_path, out_file_path, lat_min, lon_min, lat_max, lon_max, output_prefix='jaxa_sat'):
    sat_zip = zipfile.ZipFile(zip_file_path)
    sat = np.genfromtxt(sat_zip.open(os.path.basename(zip_file_path).replace('.zip', '')), delimiter=',', names=True)
    print(':',[])
    sat_filt = np.sort(
        sat[(sat['Lat'] <= lat_max) & (sat['Lat'] >= lat_min) & (sat['Lon'] <= lon_max) & (sat['Lon'] >= lon_min)],
        order=['Lat', 'Lon'])
    lats = np.sort(np.unique(sat_filt['Lat']))
    lons = np.sort(np.unique(sat_filt['Lon']))

    data = sat_filt['RainRate'].reshape(len(lats), len(lons))

    ext_utils.create_asc_file(np.flip(data, 0), lats, lons, out_file_path)

    # clevs = np.concatenate(([-1, 0], np.array([pow(2, i) for i in range(0, 9)])))
    # clevs = 10 * np.array([0.1, 0.5, 1, 2, 3, 5, 10, 15, 20, 25, 30])
    # norm = colors.BoundaryNorm(boundaries=clevs, ncolors=256)
    # cmap = plt.get_cmap('jet')
    clevs = [0, 1, 2.5, 5, 7.5, 10, 15, 20, 30, 40, 50, 75, 100, 150, 200, 250, 300]
    # clevs = [0.1, 0.5, 1, 2, 3, 5, 10, 15, 20, 25, 30, 50, 75, 100]
    norm = None
    cmap = cm.s3pcpn

    ts = dt.datetime.strptime(os.path.basename(out_file_path).replace(output_prefix + '_', '').replace('.asc', ''),
                              '%Y-%m-%d_%H:%M')
    lk_ts = utils.datetime_utc_to_lk(ts)
    title_opts = {
        'label': output_prefix + ' ' + lk_ts.strftime('%Y-%m-%d %H:%M') + ' LK\n' + ts.strftime(
            '%Y-%m-%d %H:%M') + ' UTC',
        'fontsize': 30
    }
    create_contour_plot(data, out_file_path + '.png', np.min(lats), np.min(lons), np.max(lats), np.max(lons),
                                  title_opts, clevs=clevs, cmap=cmap, norm=norm)


if __name__ == "__main__":
    zip_file_path = '/home/hasitha/PycharmProjects/Jaxa/input/gsmap_now.20190326.0430_0529.SriLanka.csv.zip'
    #zip_file_path = '/home/hasitha/PycharmProjects/Jaxa/input/gsmap_now.20190326.0430_0529.05_AsiaSS.csv.zip'
    out_file_path = '/home/hasitha/PycharmProjects/Jaxa/output/jaxa_sat_2019-03-26_04:30.asc'
    min_lat = - 3.15
    max_lat = 18.25
    min_lon = 71.15
    max_lon = 90.45
    process_jaxa_zip_file(zip_file_path, out_file_path, min_lat, min_lon, max_lat, max_lon)


