# Autonomous Drone Racing Project Course

## Installation

To run the LSY Autonomous Drone Racing project, you will need 3 additional repositories:
- [safe-control-gym](https://github.com/utiasDSL/safe-control-gym/tree/beta-iros-competition) - `beta-iros-competition` branch: The drone simulator and gym environments
- [pycffirmware](https://github.com/utiasDSL/pycffirmware) - `main` branch: A simulator for the on-board controller response of the drones we are using to accurately model their behavior
- [lsy_drone_racing](https://github.com/utiasDSL/lsy_drone_racing) - `main` branch: This repository contains the scripts to simulate and deploy the drones in the racing challenge
- [EfficientPathPlanner](https://github.com/Autonomous-Drone-Racing-Lab/Efficient-Path-Planner) C++ module with python binding for fast path and trajectory computation. 


### Create pyhthon environment
```bash
conda create -n drone python=3.8
conda activate drone
```

> **Note:** It is important you stick with **Python 3.8**. Yes, it is outdated. Yes, we'd also like to upgrade. However, there are serious issues beyond our control when deploying the code on the real drones with any other version.

Next, download the `safe-control-gym` and `pycffirmware` repositories and install them. Make sure you have your conda/mamba environment active!

```bash
cd ~/repos
git clone -b beta-iros-competition https://github.com/utiasDSL/safe-control-gym.git
cd safe-control-gym
pip install .
```

> **Note:** If you receive an error installing safe-control-gym related to gym==0.21.0, run
> ```bash
>    pip install setuptools==65.5.0 pip==21 wheel==0.38.4
> ```
> first

```bash
cd ~/repos
git clone https://github.com/utiasDSL/pycffirmware.git
cd pycffirmware
git submodule update --init --recursive
sudo apt update
sudo apt install build-essential
conda install swig
./wrapper/build_linux.sh
```

Next install the efficient path planner by following the installation tutorial as written in this repo.

Finally you can install the lsy_drone_racing package in editable mode from the repository root

```bash
cd ~/repos/lsy_drone_racing
pip install --upgrade pip
pip install -e .
```

You can test if the installation was successful by running 

```bash
cd ~/repos/lsy_drone_racing
python scripts/sim.py
```

If everything is installed correctly, this opens the simulator and simulates a drone flying through four gates.

## Configuration
All configuration is done via a config file as shown in the following. Default values are not supported and all values must be set. If unsure just use the values as provided here
```yaml
# Define the environment, gate positions, ... ----------------------
gate_id_to_name_mapping:
  1: small_portal
  0: large_portal

component_geometry:
  large_portal:
    support:
      position: [0, 0, 0.3875]
      size: [0.05, 0.05, 0.755]
      type: collision
      name: support
    bottom_bar:
      position: [0, 0, 0.75]
      size: [0.55, 0.05, 0.05]
      type: collision
      name: bottom_bar
    top_bar:
      position: [0, 0, 1.25]
      size: [0.55, 0.05, 0.05]
      type: collision
      name: top_bar
    left_bar:
      position: [-0.25, 0, 1]
      size: [0.05, 0.05, 0.55]
      type: collision
      name: left_bar
    right_bar:
      position: [0.25, 0, 1]
      size: [0.05, 0.05, 0.55]
      type: collision
      name: right_bar
    filling:
      position: [0, 0, 1.0]
      size: [0.45, 0.00000001, 0.45]
      type: filling
      name: filling
  small_portal:
    support:
      position: [0, 0, 0.15]
      size: [0.05, 0.05, 0.3]
      type: collision
      name: support
    bottom_bar:
      position: [0, 0, 0.275]
      size: [0.55, 0.05, 0.05]
      type: collision
      name: bottom_bar
    top_bar:
      position: [0, 0, 0.775]
      size: [0.55, 0.05, 0.05]
      type: collision
      name: top_bar
    left_bar:
      position: [-0.25, 0, 0.525]
      size: [0.05, 0.05, 0.55]
      type: collision
      name: left_bar
    right_bar:
      position: [0.25, 0, 0.525]
      size: [0.05, 0.05, 0.55]
      type: collision
      name: right_bar
    filling:
      position: [0, 0, 0.525]
      size: [0.45, 0.00000001, 0.45]
      type: filling
      name: filling
  obstacle:
    cylinder:
      position: [0, 0, 0.525]
      size: [0.1, 0.1, 1.05]
      type: collision
      name: obstacle

general_properties:
  takeoff_time: 0.5
  takeoff_height: 0.2
  keep_history: false

component_properties:
  large_portal:
    height: 1
  small_portal:
    height: 0.525

# End of the environment definition -------------------------------

# In the world properties, we define how our reprsentation of the world in code should look like
# The most important proerties are inflation radius. This radius states how much we inflate the volume around collision objects
# This value should at lease be as large as the radius of the drone but making it lager will make out drone more robust
world_properties:
  inflate_radius:
    gate: 0.15
    obstacle: 0.15
  lower_bound: [-3, -3, 0]
  upper_bound: [3, 3, 1.5]

# Properties definining how our C++ path planner works
path_planner_properties:
  time_limit_online: 0.3 # time we give the planner to recompute a path during flight
  time_limit_offline: 1.5 # Time we give the planner to compute a path before flight
  optimality_threshold_percentage: 0.05 # value for ompl, we preemtively stop planning if path diverges from straight line path by less than 5%
  checkpoint_gate_offset: 0.2 # we place additional checkpoints before and after each gate, this gives the distance
  range: 0.7 # max length of straight line distance used in RRT* algorithm
  min_dist_check_traj_collision: 0.1 # this is a custom inflation radius we use to check a trajectory for collision once we have new gate informatio, one strategy is to make this a bit smaller than the original ones
  min_dist_check_traj_passed_gate: 0.3 # With disturbances not all initial trajectories pass all gates, when checking if a trajectory passes a gate, it must at least pass the center of the gate by this value
  path_simplification: ompl # simplification method ompl works the best other values are none, and custom
  recalculate_online: False # For sim purpose whether we block the main thread during recomputation
  advance_for_calculation: False # For sim purpose, whether we advance trajectory for traj calculation time
  can_pass_gate: True # whether our trajectory can pass gates, i.e. fly through a gates and back through it

trajectory_generator_properties:
  type: optimal # optimal works best, other values are snap (minimum snap trajectory), spline
  max_time: 12 # only important for spline. In spline we assume same distance passed in same times, this is the time for the trajectory and timestamps are derived accordingly
  max_velocity: 2.4 # max velocity in each axis of the drone
  max_acceleration: 1.5 # max acceleration in each axis of the drone
  sampling_interval: 0.05 # How granular the trajectory is sampled

  max_traj_divergence: 0.001 # How much the trajectory is maximum allowed to diverge from the planned path (only relevant for optimal time parametization)
  prepend_traj_time: 3 # In optimal planning, we prepend trajectory with part of previous one to guarantee smooth velocities, this value defines the number of seconds to prepend

additional_statics_obstacles: [] # For constraining the solution space additional obstacles can be provided as a list


```

## Difficulty levels
The complete problem is specified by a YAML file, e.g. [`getting_started.yaml`](config/getting_started.yaml)

The config folder contains settings for progressively harder scenarios:

|         Evaluation Scenario         | Constraints | Rand. Inertial Properties | Randomized Obstacles, Gates | Rand. Between Episodes |         Notes         |
| :---------------------------------: | :---------: | :-----------------------: | :-------------------------: | :--------------------: | :-------------------: |
| [`level0.yaml`](config/level0.yaml) |   **Yes**   |           *No*            |            *No*             |          *No*          |   Perfect knowledge   |
| [`level1.yaml`](config/level1.yaml) |   **Yes**   |          **Yes**          |            *No*             |          *No*          |       Adaptive        |
| [`level2.yaml`](config/level2.yaml) |   **Yes**   |          **Yes**          |           **Yes**           |          *No*          | Learning, re-planning |
| [`level3.yaml`](config/level3.yaml) |   **Yes**   |          **Yes**          |           **Yes**           |        **Yes**         |      Robustness       |
|                                     |             |                           |                             |                        |                       |
|              sim2real               |   **Yes**   |    Real-life hardware     |           **Yes**           |          *No*          |   Sim2real transfer   |

> **Note:** "Rand. Between Episodes" (governed by argument `reseed_on_reset`) states whether randomized properties and positions vary or are kept constant (by re-seeding the random number generator on each `env.reset()`) across episodes

### Switching between configurations
You can choose which configuration to use by changing the `--config` command line option. To e.g. run the example controller on the hardest scenario, you can use the following command

```bash
python scripts/sim.py --config config/level3.yaml
```

### Common errors

#### libNatNet
If libNatNet is missing either during compiling crazyswarm or launching hover_swarm.launch, one option is to manually install it. Download the library from its [github repo](https://github.com/whoenig/NatNetSDKCrossplatform), follow the build instructions, and then add the library to your `LIBRARY_PATH` and `LD_LIBRARY_PATH` variables.

### Fly with the drones 

#### Settings
Make sure you are familiar with the configuration files. Not all options are relevant depending on the motion capture setup. For more info, see the [official documentation](https://crazyswarm.readthedocs.io/en/latest/configuration.html#adjust-configuration-files).

The important config files are located in the crazyswarm ROS package:

**TODO:** Insert correct link to files
- Crazyflies types — includes controller properties and marker configurations, etc.
- In-use Crazyflies — includes ID, radio channel, types, etc.
- All Crazyflies

As well as the launch file and Python script:

- cf_sim2real.launch
- cmdFullStateCFFirmware.py

#### Launch

>**Note:** The following is **NOT** within a conda environment, but has to run directly on the system's Python 3.8 installation. ROS has never heard of these best practices you speak of.

In a terminal, launch the ROS node for the crazyflies. Change the settings in _<path/to/crazyswarm/package>/launch/crazyflies.yaml_ as necessary.
```bash
roslaunch crazyswarm cf_sim2real.launch
```

In a second terminal:

```bash
python scripts/deploy.py --controller <path/to/your/controller.py> --config config/level3.yaml
```

where `<path/to/your/controller.py>` implements a controller that inherits from `lsy_drone_racing.controller.BaseController`


