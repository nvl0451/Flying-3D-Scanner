# Indicate the openMVG binary directory
OPENMVG_SFM_BIN = "PATH_TO_OPENMVG_BIN"
OPENMVG_SRC = "PATH_TO_OPENMVG_SRC"
OPENMVS_BIN = "PATH_TO_OPENMVS_BIN"


# Indicate the openMVG camera sensor width directory
CAMERA_SENSOR_WIDTH_DIRECTORY = OPENMVG_SRC + "/../../openMVG/exif/sensor_width_database"

import os
import subprocess
import sys

sparse_name = ""

if len(sys.argv) != 3:
    print ("Usage %s sparse_name session_name" % sys.argv[0])
    print("sparse_name must be MVG (recommended) or COLMAP")
    sys.exit(1)

if (sys.argv[1] == "MVG" or sys.argv[1] == "COLMAP"):
    sparse_name = sys.argv[1]
else:
    print("Usage %s sparse_name session_name" % sys.argv[0])
    print("sparse_name must be MVG (recommended) or COLMAP!")
    sys.exit(1)

dir = sys.argv[2]
input_dir = os.path.join(dir, "images")
output_dir = os.path.join(dir, "MVG")
matches_dir = os.path.join(output_dir, "matches")
reconstruction_dir = os.path.join(output_dir, "reconstruction_sequential")
camera_file_params = os.path.join(CAMERA_SENSOR_WIDTH_DIRECTORY, "sensor_width_camera_database.txt")

print ("Using input dir  : ", input_dir)
print ("      output_dir : ", output_dir)

if sparse_name == "MVG":
    # Create the ouput/matches folder if not present
    if not os.path.exists(output_dir):
      os.mkdir(output_dir)
    if not os.path.exists(matches_dir):
      os.mkdir(matches_dir)

    print ("1. Intrinsics analysis")
    pIntrisics = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_SfMInit_ImageListing"),  "-i", input_dir, "-o", matches_dir, "-d", camera_file_params, "-c", "3", "-f", "1980"] )
    pIntrisics.wait()

    print ("2. Compute features")
    pFeatures = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeFeatures"),  "-i", matches_dir+"/sfm_data.json", "-o", matches_dir, "-m", "SIFT"] )
    pFeatures.wait()

    print ("3. Compute matching pairs")
    pPairs = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_PairGenerator"), "-i", matches_dir+"/sfm_data.json", "-o" , matches_dir + "/pairs.bin" ] )
    pPairs.wait()

    print ("4. Compute matches")
    pMatches = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeMatches"),  "-i", matches_dir+"/sfm_data.json", "-p", matches_dir+ "/pairs.bin", "-o", matches_dir + "/matches.putative.bin" ] )
    pMatches.wait()

    print ("5. Filter matches" )
    pFiltering = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_GeometricFilter"), "-i", matches_dir+"/sfm_data.json", "-m", matches_dir+"/matches.putative.bin" , "-g" , "f" , "-o" , matches_dir+"/matches.f.bin" ] )
    pFiltering.wait()

    # Create the reconstruction if not present
    if not os.path.exists(reconstruction_dir):
        os.mkdir(reconstruction_dir)

    print ("6. Do Sequential/Incremental reconstruction")
    pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_SfM"), "--sfm_engine", "INCREMENTAL", "--input_file", matches_dir+"/sfm_data.json", "--match_dir", matches_dir, "--output_dir", reconstruction_dir] )
    pRecons.wait()

    print ("7. Colorize Structure")
    pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeSfM_DataColor"),  "-i", reconstruction_dir+"/sfm_data.bin", "-o", os.path.join(reconstruction_dir,"colorized.ply")] )
    pRecons.wait()

    print("8. MVG to MVS transition")
    pTrans = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_openMVG2openMVS"),  "-i", reconstruction_dir+"/sfm_data.bin", "-o", os.path.join(dir,"scene.mvs"), "-d", os.path.join(reconstruction_dir,"scene_undistorted_images")])
    pTrans.wait()
else:
    print("1. Feature Extraction")
    pFeature = subprocess.Popen(["colmap", "feature_extractor", "--database_path", "database.db", "--image_path", "images"], cwd=dir)
    pFeature.wait()

    print("2. Exhaustive Matching")
    pMatching = subprocess.Popen(["colmap", "exhaustive_matcher", "--database_path", "database.db"], cwd=dir)
    pMatching.wait()

    pMkdir = subprocess.Popen(["mkdir", "sparse"], cwd=dir)
    pMkdir.wait()

    print("3. Mapping")
    pMapping = subprocess.Popen(["colmap", "mapper", "--database_path", "database.db", "--image_path", "images", "--output_path", "sparse"], cwd=dir)
    pMapping.wait()

    pMkdir2 = subprocess.Popen(["mkdir", "dense"], cwd=dir)
    pMkdir2.wait()

    print("4. Image Undistorting")
    pMapping = subprocess.Popen(
        ["colmap", "image_undistorter", "--image_path", "images", "--input_path", "sparse/0", "--output_path", "dense", "--output_type", "COLMAP", "--max_image_size", "2000"],
        cwd=dir)
    pMapping.wait()

    print("5. Colmap to MVS transition")
    pTrans = subprocess.Popen(
        [os.path.join(OPENMVS_BIN, "InterfaceCOLMAP"), "-i", "dense",
         "-o", "scene.mvs", "--image-folder", "dense/images"], cwd=dir)
    pTrans.wait()


print("9. Densify Point Cloud")
pDense = subprocess.Popen( [os.path.join(OPENMVS_BIN, "DensifyPointCloud"), "scene.mvs"], cwd=dir)
pDense.wait()

print("9. Reconstruct Mesh")
pDense = subprocess.Popen( [os.path.join(OPENMVS_BIN, "ReconstructMesh"), "scene_dense.mvs", "-p", "scene_dense.ply"], cwd=dir)
pDense.wait()

print("9. Refine Mesh")
pRefine = subprocess.Popen( [os.path.join(OPENMVS_BIN, "RefineMesh"), "scene_dense.mvs", "-m", "scene_dense_mesh.ply"], cwd=dir)
pRefine.wait()

print("9. Refine Mesh")
pTexture = subprocess.Popen( [os.path.join(OPENMVS_BIN, "TextureMesh"), "--export-type", "glb", "scene_dense.mvs", "-m", "scene_dense_refine.ply"], cwd=dir)
pTexture.wait()