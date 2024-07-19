# Fix, so we can import form the src module
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.experiment_trakcer import Experiment
from src.visualization_utils.map.map import Map
from src.visualization_utils.utils.config_reader import ConfigReader





import numpy as np
import matplotlib.pyplot as plt
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

def parse_experiments(path):
    with open(path, "rb") as f:
        experiments = pickle.load(f)
        if isinstance(experiments[0], dict):
            print(f"Restoring from dirct")
            experiments = [Experiment.from_dict(experiment) for experiment in experiments]

    return experiments


if __name__ == "__main__":
    config_path = "./config.yaml"
    config_reader = ConfigReader.create(config_path=config_path)

    nominal_gates_pos_and_type = parse_objects("./path_segments/gates.txt")
    nomial_obstacle_pos = parse_objects("./path_segments/obstacles.txt")

    # create map and parse objects
    lower_bound = np.array([-1.0, -2, 0])
    upper_bound = np.array([1.5, 1.5, 2])

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
    experiment_file1 = "/home/tim/code/lsy_drone_racing/documentation/drawing/experiment_optim.pkl"
    experiment_file2 = "/home/tim/code/lsy_drone_racing/documentation/drawing/experiment_rl.pkl"
    experiments_1 = parse_experiments(experiment_file1)
    experiments_2 = parse_experiments(experiment_file2)
    experiment_1 = experiments_1[0]
    experiment_2 = experiments_2[0]

    
    ax = map.create_map_sized_figure()
    ax.w_zaxis.line.set_lw(0.)
    ax.set_zticks([])
    # remove z label
    ax.set_zlabel('')

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
    for experiment in [experiment_1, experiment_2]:
        obs = experiment.get_drone_pos()
        ax.plot(obs[:, 0], obs[:, 1], obs[:, 2], label="test")

    #ax.legend()

    save_path = "documentation/drawing/comparison"
    save_png = save_path + ".png"
    save_eps = save_path + ".eps"
    plt.savefig(save_png, bbox_inches='tight')
    plt.savefig(save_eps, bbox_inches='tight', format='eps')
    # plt.show()
