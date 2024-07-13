TEMP_DIR = "./temp"
from copy import deepcopy
import optuna
import yaml
import sys
import os
from sim import simulate
import numpy as np
from optuna.samplers import RandomSampler

import logging
logger = logging.getLogger("hp_search")


def create_config(config, temp_dir, max_vel, max_acc):
    config = deepcopy(config)

    temp_path = os.path.join(temp_dir, "config_optimal.yaml")
    
    config["trajectory_generator_properties"]["max_velocity"] = max_vel
    config["trajectory_generator_properties"]["max_acceleration"] = max_acc

    with open(temp_path, "w") as file:
        yaml.dump(config, file)
    
    return temp_path



def objective(trial):
    CONFIG_PATH = "./hp_base_config_optimal_no_gate_pass.yaml"
    #CONFIG_PATH = "./hp_base_config_optimal.yaml"
    TEMP_DIR = "./temp"
    controller = "src/my_controller_cpp.py"
    task_config = "config/level1.yaml"
    N_RUNS = 50

    with open (CONFIG_PATH, "r") as file:
        config = yaml.safe_load(file)

    
    max_vel = trial.suggest_float("max_velocity", 4.0, 4.7)
    max_acc = trial.suggest_float("max_acceleration", 2.7, 3.2)
  
    controller_config = create_config(config, TEMP_DIR, max_vel, max_acc)

    ep_times = simulate(config=task_config, controller=controller, n_runs=N_RUNS, gui=False, controller_config=controller_config)
    # mark this trial as failed
    failed_runs = len([x for x in ep_times if x is None])
    success_rate = (N_RUNS - failed_runs) / N_RUNS    
    ep_times = np.array([x for x in ep_times if x is not None])
    if len(ep_times) == 0:
        logger.info(f"Experiment failed all runs. Params: max_vel: {max_vel}, max_acc: {max_acc}")
        return None
    # find median time
    best_time = np.min(ep_times)
    meadian_time = np.median(ep_times)
    mean_time = np.mean(ep_times)
    std_time = np.std(ep_times)
    
    logger.info(f"Experiment completed with best_time: {best_time} median_time: {meadian_time}, mean time: {mean_time} and std time: {std_time}. The success rate was: {success_rate}. Parameters: max_vel: {max_vel}, max_acc: {max_acc}")

    return meadian_time


if __name__ == "__main__":

    log_path = "temp/hp_search_optimal_no_gate_pass.log"
    #log_path = "temp/hp_search_optimal.log"
    file_handler = logging.FileHandler(log_path, mode="w")
    console_handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    sampler = optuna.samplers.RandomSampler()
    study = optuna.create_study(direction="minimize", sampler=sampler)
    study.optimize(objective, n_trials=50)
    logger.info(f"BEst value is {study.best_value}")
    logger.info(f"Best params are {study.best_params}")

    
