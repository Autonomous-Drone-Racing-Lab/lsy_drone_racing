# Fix, so we can import form the src module
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.visualization_utils.map.map import Map
from src.visualization_utils.utils.config_reader import ConfigReader
import numpy as np
from src.visualization_utils.utils.types import Gate, Obstacle
import re

def parse_objects(path):
    gates_pos = {}
    with open(path, "r") as f:
        for line in f:
            numbers = numbers = re.findall(r"-?\d+\.\d+|-?\d+", line)
            id = int(numbers[0])
            info = [float(x) for x in numbers[1:]]
            gates_pos[id] = info
    res = []
    for i in range(len(gates_pos.values())):
        val = gates_pos[i]
        res.append(val)
    
    return np.array(res)

def parse_checkpoints(path):
    checkpoints = []
    with open(path, "r") as f:
        for line in f:
            numbers = re.findall(r"-?\d+\.\d+|-?\d+", line)
            info = [float(x) for x in numbers]
            checkpoints.append(info)
    return np.array(checkpoints)


if __name__ == "__main__":
    config_path = "./config.yaml"
    config_reader = ConfigReader.create(config_path=config_path)

    nominal_gates_pos_and_type = parse_objects("./path_segments/gates.txt")
    nomial_obstacle_pos = parse_objects("./path_segments/obstacles.txt")
    checkpoints = parse_checkpoints("./path_segments/checkpoints.txt")

    # create map and parse objects
    lower_bound = np.array([-2, -2, 0])
    upper_bound = np.array([2, 2, 2])

    map = Map(lower_bound, upper_bound)
    
    gates = []
    for gate in nominal_gates_pos_and_type:
        gates.append(Gate.from_nomial_gate_pos_and_type(gate))
    
    obstacles = []
    for obstacle in nomial_obstacle_pos:
        obstacles.append(Obstacle.from_obstacle_pos(obstacle))
    
    map.parse_gates(gates)
    map.parse_obstacles(obstacles)

    import pickle
    traj_file = "traj.pkl"
    with open(traj_file, "rb") as f:
        trajs = pickle.load(f)

    paths = []
    for traj in trajs:
        x_idx = 0
        y_idx = 3
        z_idx = 6
        path = traj[:, [x_idx, y_idx, z_idx]]
        paths.append(path)

    map.draw_scene(paths)
