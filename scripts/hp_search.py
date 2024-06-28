TEMP_DIR = "./temp"
import optuna
import yaml
import sys
import os
from sim import simulate
import numpy as np

import logging
logger = logging.getLogger("hp_search")


def create_config(config_path, temp_dir, planner_algo, max_vel, max_acc):
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    temp_path = os.path.join(temp_dir, "config.yaml")
    
    config["path_planner_properties"]["planner_algo"] = planner_algo
    config["path_planner_properties"]["max_velocity"] = max_vel
    config["path_planner_properties"]["max_acceleration"] = max_acc

    with open(temp_path, "w") as file:
        yaml.dump(config, file)
    
    return temp_path



def objective(trial):
    CONFIG_PATH = "./hp_base_config.yaml"
    TEMP_DIR = "./temp"
    controller = "src/my_controller_cpp.py"
    task_config = "config/level3.yaml"
    N_RUNS = 25

    planner_algo = trial.suggest_categorical("planner_algo", ["rrt", "fmt"])
    max_vel = trial.suggest_float("max_velocity", 2, 5)
    max_acc = trial.suggest_float("max_acceleration", 1, 4)
    controller_config = create_config(CONFIG_PATH, TEMP_DIR, planner_algo, max_vel, max_acc)

    logger.info(f"Starting new experiment with params algo: {planner_algo}, max_vel: {max_vel}, max_acc: {max_acc}")
    ep_times = simulate(config=task_config, controller=controller, n_runs=N_RUNS, gui=False, controller_config=controller_config)
    # mark this trial as failed
    failed_runs = len([x for x in ep_times if x is None])
    if failed_runs > N_RUNS / 2:
        logger.info(f"Experiment failed with {failed_runs} runs out of {N_RUNS}")
        return 1000
    
    ep_times = np.array([x for x in ep_times if x is not None])
    # find median time
    meadian_time = np.median(ep_times)
    mean_time = np.mean(ep_times)
    success_rate = (N_RUNS - failed_runs) / N_RUNS
    logger.info(f"Experiment completed with median_time: {meadian_time} and mean time: {mean_time}. The success rate was: {success_rate}")

    return meadian_time


if __name__ == "__main__":

    log_path = "temp/hp_search.log"
    file_handler = logging.FileHandler(log_path, mode="w")
    console_handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=100)
    logger.info(f"BEst value is {study.best_value}")
    logger.info(f"Best params are {study.best_params}")

    
