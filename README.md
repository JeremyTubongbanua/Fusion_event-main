# Fusion_event


## 🔍 Problem

Autonomous vehicles rely on sensors like LiDAR and cameras to perceive their environment. Each sensor has strengths and limitations:

🔹 LiDAR provides accurate 3D data but lacks color information.

🔹 Cameras capture rich visuals but are sensitive to lighting conditions.


Individually, these sensors can be noisy or miss key details due to occlusions from other road agents. However, by fusing data from multiple sensors and vehicles, we can create a more reliable, comprehensive view of the scene, improving safety and awareness.

## 🚦 Scenario

Two self-driving cars are approaching an intersection, each equipped with:


✅ 3D LiDAR

✅ Camera

The environment includes vehicles, pedestrians, and cyclists, some of whom may block each vehicle’s view. By communicating and sharing sensor data, the vehicles can collaborate to overcome occlusions and enhance situational understanding.

![scene](/images/scene.png)

The camera Intrinsic Matrix is
``` 
  2058.72664   ,  0           , 960
  0            , 2058.72664   , 540
  0            , 0            , 1
```
## Dataset Description

The [/data/input](/data/input) folder contains a JSON metadata file for each scene. Each JSON file contains the following information

| Field | Description | Unit |
| --- | --- | --- |
| CarA_Camera | Path to the image captured by the first vehicle's camera |  |
| CarA_Lidar | Path to the point cloud captured by the first vehicle's Lidar|  |
| CarA_Location | The location of the center of the first vehicle (x, y) | meters |
| CarA_Rotation | The rotation of the first vehicle | degree |
| CarA_Dimension | The dimensions of the first vehicle (Length, Width, Height) | m |
| CarB_Camera | Path to the image captured by the second vehicle's camera |  |
| CarB_Lidar | Path to the point cloud captured by the second vehicle's Lidar|  |
| CarB_Location | The location of the center of the second vehicle (x, y) | meters |
| CarB_Rotation | The rotation of the second vehicle | degree |
| CarB_Dimension | The dimensions of the second vehicle (Length, Width, Height) | meters |

The [/data/output](/data/output) folder contains JSON files of all other road agents in the scene. Each JSON file contains an array of 

| Field | Description | Unit |
| --- | --- | --- |
| Object | the type of road agents (Car/Pedestrian) |  |
| Location | The location of the center of the road agent (x, y) | meters |
| Rotation | The rotation of the road agent | degree |
| Dimension | The dimensions of the road agent (Length, Width, Height) | meters |

  ## 🎯 Goal

Process the raw camera and LiDAR data from both vehicles to:


🔹 Generate individual object detection outputs for each car.

🔹 Fuse the data to build a shared perception of the scene.

🔹 Enhance visibility by addressing sensor occlusions and inconsistencies.

🔹 Output a visual representation showing detected agents from both perspectives.
