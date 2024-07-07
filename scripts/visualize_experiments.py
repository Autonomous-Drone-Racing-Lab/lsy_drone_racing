# Fix, so we can import form the src module
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.experiment_trakcer import Experiment
from src.map.map import Map
from src.utils.config_reader import ConfigReader
import numpy as np
import matplotlib.pyplot as plt
import yaml
from src.utils.types import Gate, Obstacle
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
    experiment_file = "experiments.pkl"
    with open(experiment_file, "rb") as f:
        experiments = pickle.load(f)
        if isinstance(experiments[0], dict):
            print(f"Restoring from dirct")
            experiments = [Experiment.from_dict(experiment) for experiment in experiments]

    
    ax = map.create_map_sized_figure()

    show_checkpoints = True
    if show_checkpoints:
        checkpoints = parse_checkpoints("./path_segments/checkpoints.txt")
        for checkpoint in checkpoints[1:-1]:
            ax.scatter(checkpoint[0], checkpoint[1], checkpoint[2], c='r', marker='x')


    # set camera position, looo along x axis 45 degree from top
    #ax.view_init(elev=55, azim=0)
    # set top down view
    ax.view_init(elev=90, azim=0)

    map.add_objects_to_plot(ax)
    for experiment in experiments:
        obs = experiment.get_drone_pos()
        ax.plot(obs[:, 0], obs[:, 1], obs[:, 2])

    save_path = "documentation/drawing/experiment_optim_checkpoints"
    save_png = save_path + ".png"
    save_eps = save_path + ".eps"
    save_exp = save_path + ".pkl"
    plt.savefig(save_png, bbox_inches='tight')
    plt.savefig(save_eps, bbox_inches='tight', format='eps')
    # copy the experiment file to the documentation folder
    import shutil
    shutil.copyfile(experiment_file, save_exp)
    # plt.show()
