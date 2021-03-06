import open3d
import numpy as np
import glob
import copy
import time
import numpy.linalg
import mrob


# Save pcd to png file. You have 5 seconds to rotate pcd for preferred position.
def save_pcd_to_png(name, pcd):
    vis = open3d.visualization.Visualizer()
    vis.create_window()
    vis.add_geometry(pcd)
    vis.update_geometry()
    vis.poll_events()
    vis.update_renderer()
    vis.run()
    time.sleep(5)
    vis.capture_screen_image(name)
    vis.destroy_window()


def find_transformation(source, target, trans_init):
    threshold = 0.2
    if not source.has_normals():
        source.estimate_normals(search_param=open3d.geometry.KDTreeSearchParamHybrid(
            radius=0.5, max_nn=50))
    if not target.has_normals():
        target.estimate_normals(search_param=open3d.geometry.KDTreeSearchParamHybrid(
            radius=0.5, max_nn=50))
    transformation = open3d.registration.registration_icp(source, target, threshold
        , trans_init,open3d.registration.TransformationEstimationPointToPlane()).transformation
    return transformation


# To execute: main.py <directory to pcd-files>
if __name__ == '__main__':
    files = glob.glob('./pcds/*.pcd')
    print(len(files))
    files.sort()
    files = files[:300]

    pcds = []
    print(files[0])
    for file in files:
        pcds.append(open3d.io.read_point_cloud(file))

    trans_sum_approximation = np.eye(4)
    pcd_full = [pcds[0]]
    cnt = 0
    for i in range(0, 270):
        trans = find_transformation(pcds[i + 1], pcds[i], np.eye(4))
        trans_sum_approximation = trans @ trans_sum_approximation
        res_trans = find_transformation(pcds[i + 1], pcd_full[-1], trans_sum_approximation)
        trans_sum_approximation = res_trans
        # Above we calculate approximation, error can be increased if we apply this transformation directly
        # Therefore the second estimation (below) for transformation is used
        # Also this approximation will be useful when skipping some frames
        if numpy.linalg.norm(mrob.SE3(trans).ln()) < 0.03:
            cnt += 1
            print(i)
            source = copy.deepcopy(pcds[i + 1]).transform(res_trans)
            pcd_full.append(source)

    print(cnt)
    open3d.visualization.draw_geometries(pcd_full)
