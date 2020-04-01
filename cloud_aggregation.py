import numpy as np
path = r"mrob/lib"
import sys
sys.path.append(path)
import mrob
import copy
import math
import open3d
import glob
import os
import deprecation
from collections import defaultdict






def rectify(source, transformation, timestamp, discr_count=10):
    """

    :param source:
    :param transformation:
    :param discr_count:
    :return: open3d pcd object
    """
    timestamp_split = split_by_timestamp(source, timestamp)
    # discretization_splited = split_in_groups(timestamp_split, discr_count)
    # aggregated_cloud = rectify_groups(discretization_splited, transformation)

    aggregated_cloud = rectify_pcds(timestamp_split, transformation)
    aggregated_pcd = np.zeros((0, 3))
    for pcd in aggregated_cloud:
        aggregated_pcd = np.vstack((aggregated_pcd, pcd.points))
    pcd = open3d.geometry.PointCloud()
    pcd.points = open3d.utility.Vector3dVector(copy.deepcopy(aggregated_pcd))
    pcd.paint_uniform_color([0, 1, 0])
    return pcd




def rectify_pcds(source_groups, transformation):
    res = []
    transformation = mrob.SE3(transformation).ln()
    for tau in source_groups.keys():
        T = mrob.SE3((tau * transformation))# интерполяция компенационного перехода
        pcd = open3d.geometry.PointCloud()
        pcd.points = open3d.utility.Vector3dVector(copy.deepcopy(source_groups[tau]))
        pcd.transform(T.T())
        res.append(copy.deepcopy(pcd))

    return res



@deprecation.deprecated(details="Use the rectify_pcds function instead")
def rectify_groups(source_groups, transformation):
    discr_cnt = len(source_groups)
    xi_ini = np.array([0, 0, 0, 0, 0, 0], dtype='float64')
    xi_fin = mrob.SE3(transformation).ln()
    xi = np.zeros((discr_cnt, 6))
    for i in range(6):
        xi[:, i] = np.linspace(xi_ini[i], xi_fin[i], discr_cnt, dtype='float64')
    res = []
    for i in range(discr_cnt):
        new_one = copy.deepcopy(source_groups[i]).transform(mrob.SE3(xi[i, :]).inv().T())
        res.append(new_one.paint_uniform_color([1, 0.706, 0]))

    return res

@deprecation.deprecated(details="Use the rectify_pcds function instead")
def split_in_groups(timestamps_split, discr_cnt = 10):
    ln = math.ceil(len(timestamps_split) / discr_cnt)
    pcds = []
    for i in range(discr_cnt):
        pcd = open3d.geometry.PointCloud()
        xyz = []
        for j in range(ln):
            ind = i * ln + j
            if ind < len(timestamps_split):
                group = timestamps_split[ind]
                for k in range(len(group)):
                    xyz.append(group[k])
        arr = np.array(xyz)
        # There maybe some problems with the last array, therefore check is needed
        if len(arr) != 0:
            # print(arr)
            pcd.points = open3d.utility.Vector3dVector(arr)
            pcds.append(copy.deepcopy(pcd.paint_uniform_color([0, 0, 1])))
    return pcds


def split_by_timestamp(source, colors):
    points = np.asarray(source.points)
    print(len(colors), len(points))
    pcd_split = dict()
    new_group = []
    prev_color = colors[0]
    for i in range(len(colors)):
        curr_color = colors[i]
        eq = True
        if curr_color != prev_color:
            eq = False
        if eq:
            new_group.append(copy.deepcopy(points[i]))
        else:
            pcd_split[prev_color] = new_group
            new_group = []
        prev_color = curr_color
    return pcd_split

files = []
path = r"data/2020-01-21/formatted" # example of folder with pcds

if __name__ == '__main__':
    from main import find_transformation

    for (dirpath, dirnames, filenames) in os.walk(path):
        for file in filenames:
            files.append(os.path.join(dirpath, file))

    files.sort()
    files = files[:155]
    #
    pcds = []
    timestamps = []
    for file in files:
        data = np.genfromtxt(file, skip_header=11, delimiter= " ")
        timestamps.append(data[:, -1])
        pcd = open3d.geometry.PointCloud()
        pcd.points = open3d.utility.Vector3dVector(data[:,:3])
        pcds.append(open3d.io.read_point_cloud(file, format="pcd"))
    #
    #
    # # for i in range(40):


    transformation = find_transformation(pcds[150], pcds[149], np.eye(4))
    aggregated_cloud = rectify(pcds[150], transformation, timestamp = timestamps[150])

    # path = os.path.join(os.path.dirname(path), "rectified/150.pcd")
    # p_rectified_old = open3d.io.read_point_cloud(path, format="pcd")
    # p_rectified_old.paint_uniform_color([1, 0, 0])
    open3d.visualization.draw_geometries([pcds[150], aggregated_cloud])


