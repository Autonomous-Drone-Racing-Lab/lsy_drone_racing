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

Next install the efficient path planner by following the installation tutorial as written in [its repo](https://github.com/Autonomous-Drone-Racing-Lab/Efficient-Path-Planner).

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
All configuration is done via a config file as shown `controller_config/`. Default values are not supported and all values must be set. If unsure just use the values as provided here

## Execution
Run the code via `python scripts/sim.py` providing all relevant information as command line arguments. At leas always provide the `config` and the `controller_config`

To test a controller over many runs and collect results, you can use `python scripts/kaggle.py`, where you must add the desired configuration within the file
