# Fix, so we can import form the src module
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.visualization_utils.map.map import Map
from src.visualization_utils.utils.config_reader import ConfigReader
import numpy as np
import yaml
from src.visualization_utils.utils.types import Gate, Obstacle


if __name__ == "__main__":
    config_path = "./config.yaml"
    config_reader = ConfigReader.create(config_path=config_path)


    #task path
    path = "./task.yaml"
    # parse file
    with open(path) as f:
        task = yaml.safe_load(f)
    

    nominal_gates_pos_and_type = task["nominal_gates_pos_and_type"]
    nominal_gates_pos_and_type = np.array(nominal_gates_pos_and_type)
    nomial_obstacle_pos = task["nomial_obstacle_pos"]
    nomial_obstacle_pos = np.array(nomial_obstacle_pos)
    chekpoints = task["chekpoints"]
    chekpoints = np.array(chekpoints)

    path_file = "path_segments/path_4900.txt"
    # path is stored as list of points coordinates comma separated
    with open(path_file, "r") as f:
        path = f.readlines()
        path = [point.strip().split(" ") for point in path]
        path = np.array(path, dtype=float)

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

    # plot map
    map.draw_scene(path=path)

