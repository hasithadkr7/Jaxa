from datetime import datetime, timedelta
import os
import zipfile
import math
import matplotlib
import mpl_toolkits.basemap as Basemap
from matplotlib import rcParams, colors
LUTSIZE = rcParams['image.lut']
matplotlib.use('Agg')
import matplotlib
import numpy as np
from joblib import Parallel, delayed
from mpl_toolkits.basemap import cm

matplotlib.use('Agg')
from matplotlib import colors, pyplot as plt

def create_asc_file(data, lats, lons, out_file_path, cell_size=0.1, no_data_val=-99, overwrite=False):
    with open(out_file_path, 'wb') as out_file:
        out_file.write(('NCOLS %d\n' % len(lons)).encode())
        out_file.write(('NROWS %d\n' % len(lats)).encode())
        out_file.write(('XLLCORNER %f\n' % lons[0]).encode())
        out_file.write(('YLLCORNER %f\n' % lats[0]).encode())
        out_file.write(('CELLSIZE %f\n' % cell_size).encode())
        out_file.write(('NODATA_VALUE %d\n' % no_data_val).encode())
        np.savetxt(out_file, data, fmt='%.4f')


def create_contour_plot(data, out_file_path, lat_min, lon_min, lat_max, lon_max, plot_title, basemap=None, clevs=None,
                        cmap=plt.get_cmap('Reds'), overwrite=False, norm=None, additional_changes=None, **kwargs):
    """
    create a contour plot using basemap
    :param additional_changes:
    :param norm:
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

    # cs = basemap.contourf(lons, lats, data, clevs, cmap=cm.s3pcpn_l, latlon=True)
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
    # fig.savefig(out_file_path)
    plt.close()


def datetime_utc_to_lk(timestamp_utc, shift_mins=0):
    return timestamp_utc + timedelta(hours=5, minutes=30 + shift_mins)



lat_min = max(-4.0, -3.06107)
lon_min = max(60.0, 71.2166)
lat_max = min(40.0, 18.1895)
lon_max = min(93.0, 90.3315)
output_prefix = 'jaxa_sat'
prefix = datetime.now().strftime('%Y-%m-%d_%H:%M')
out_file_path = '/home/hasitha/PycharmProjects/Jaxa/output/Map{}.asc'.format(prefix)
zip_file_path = '/home/hasitha/PycharmProjects/Jaxa/input/gsmap_now.20190123.0530_0629.05_AsiaSS.csv.zip'
sat_zip = zipfile.ZipFile(zip_file_path)
sat = np.genfromtxt(sat_zip.open(os.path.basename(zip_file_path).replace('.zip', '')), delimiter=',', names=True)
print('sat:', sat)
sat_filt = np.sort(
    sat[(sat['Lat'] <= lat_max) & (sat['Lat'] >= lat_min) & (sat['Lon'] <= lon_max) & (sat['Lon'] >= lon_min)],
        order=['Lat', 'Lon'])
lats = np.sort(np.unique(sat_filt['Lat']))
lons = np.sort(np.unique(sat_filt['Lon']))

data = sat_filt['RainRate'].reshape(len(lats), len(lons))

create_asc_file(np.flip(data, 0), lats, lons, out_file_path)

cmap = plt.get_cmap('jet')
clevs = [0, 1, 2.5, 5, 7.5, 10, 15, 20, 30, 40, 50, 75, 100, 150, 200, 250, 300]
norm = None
# cmap = colors.LinearSegmentedColormap('s3pcpn', s3pcpn_data, LUTSIZE)

ts = datetime.strptime('2018-01-23_15:00', '%Y-%m-%d_%H:%M')
lk_ts = ts + timedelta(hours=5, minutes=30)
title_opts = {
   'label': output_prefix + ' ' + lk_ts.strftime('%Y-%m-%d %H:%M') + ' LK\n' + ts.strftime(
       '%Y-%m-%d %H:%M') + ' UTC',
        'fontsize': 30
}

print('np.min(lats):', np.min(lats))
print('np.min(lons):', np.min(lons))
print('np.max(lats):', np.max(lats))
print('np.max(lons):', np.max(lons))
# create_contour_plot(data, out_file_path + '.png', np.min(lats), np.min(lons), np.max(lats), np.max(lons),
#                                   title_opts, clevs=clevs, cmap=cmap, norm=norm)
create_contour_plot(data, out_file_path + '.png', np.min(lats), np.min(lons), np.max(lats), np.max(lons),
                                  title_opts)

