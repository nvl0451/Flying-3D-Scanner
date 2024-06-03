import av
import cv2
import numpy as np
import open3d as o3d
import tellopy


# Function to extract keypoints and descriptors
def extract_features(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    orb = cv2.ORB_create()
    keypoints, descriptors = orb.detectAndCompute(gray, None)
    return keypoints, descriptors


# Function to match features between two frames
def match_features(desc1, desc2):
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(desc1, desc2)
    matches = sorted(matches, key=lambda x: x.distance)
    return matches

# Initialize video stream
drone = tellopy.Tello()
drone.connect()
container = av.open(drone.get_video_stream())

# Initialize Open3D visualizer
vis = o3d.visualization.Visualizer()
vis.create_window()

# Main loop
prev_frame = None
prev_keypoints = None
prev_descriptors = None
points = []

streaming = True
while streaming:
    for frame in container.decode(video=0):
        img = frame.to_ndarray(format='bgr24')

        # Extract features from the current frame
        keypoints, descriptors = extract_features(img)

        if prev_frame is not None:
            # Match features between the previous and current frames
            matches = match_features(prev_descriptors, descriptors)

            # Extract matched keypoints
            src_pts = np.float32([prev_keypoints[m.queryIdx].pt for m in matches]).reshape(-1, 2)
            dst_pts = np.float32([keypoints[m.trainIdx].pt for m in matches]).reshape(-1, 2)

            # Estimate the essential matrix and recover pose
            E, mask = cv2.findEssentialMat(dst_pts, src_pts, focal=1.0, pp=(0.0, 0.0), method=cv2.RANSAC, prob=0.999,
                                           threshold=1.0)
            _, R, t, mask = cv2.recoverPose(E, dst_pts, src_pts)

            # Triangulate points
            pts4D = cv2.triangulatePoints(np.hstack((np.eye(3), np.zeros((3, 1)))), np.hstack((R, t)), src_pts.T,
                                          dst_pts.T)
            pts3D = pts4D[:3] / pts4D[3]
            points.append(pts3D.T)

            # Update point cloud in Open3D visualizer
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(np.vstack(points))
            vis.clear_geometries()
            vis.add_geometry(pcd)
            vis.poll_events()
            vis.update_renderer()

        # Update previous frame and keypoints
        prev_frame = img
        prev_keypoints = keypoints
        prev_descriptors = descriptors

vis.destroy_window()
