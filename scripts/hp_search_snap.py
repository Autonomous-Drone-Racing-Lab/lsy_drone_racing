TEMP_DIR = "./temp"
import optuna
import yaml
import sys
import os
from sim import simulate
import numpy as np
from optuna.samplers import RandomSampler

import logging
logger = logging.getLogger("hp_search")


def create_config(config_path, temp_dir, planner_algo, max_vel, max_acc, checkpoint_offset, can_pass_gate):
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    temp_path = os.path.join(temp_dir, "config.yaml")
    
    #config["path_planner_properties"]["planner_algo"] = planner_algo
    config["trajectory_generator_properties"]["max_velocity"] = max_vel
    config["trajectory_generator_properties"]["max_acceleration"] = max_acc
    config["path_planner_properties"]["checkpoint_offset"] = checkpoint_offset
    config["path_planner_properties"]["can_pass_gate"] = can_pass_gate

    with open(temp_path, "w") as file:
        yaml.dump(config, file)
    
    return temp_path



def objective(trial):
    CONFIG_PATH = "./hp_base_config.yaml"
    TEMP_DIR = "./temp"
    controller = "src/my_controller_cpp.py"
    task_config = "config/level3.yaml"
    N_RUNS = 20

    planner_algo = trial.suggest_categorical("planner_algo", ["rrt", "fmt"])
    can_pass_gate = True# trial.suggest_categorical("can_pass_gate", [True, False])
    max_vel = trial.suggest_float("max_velocity", 3.5, 5)
    max_acc = trial.suggest_float("max_acceleration", 3, 5)
    checkpoint_offset = trial.suggest_float("checkpoint_offset", 0.05, 0.15)
    controller_config = create_config(CONFIG_PATH, TEMP_DIR, planner_algo, max_vel, max_acc, checkpoint_offset, can_pass_gate)

    ep_times = simulate(config=task_config, controller=controller, n_runs=N_RUNS, gui=False, controller_config=controller_config)
    # mark this trial as failed
    failed_runs = len([x for x in ep_times if x is None])
    success_rate = (N_RUNS - failed_runs) / N_RUNS    
    ep_times = np.array([x for x in ep_times if x is not None])
    if len(ep_times) == 0:
        logger.info(f"Experiment failed all runs. Params: algo: {planner_algo}, max_vel: {max_vel}, max_acc: {max_acc}, checkpoint_offset: {checkpoint_offset}  can_pass_gate: {can_pass_gate}")
        return None
    # find median time
    best_time = np.min(ep_times)
    meadian_time = np.median(ep_times)
    mean_time = np.mean(ep_times)
    
    logger.info(f"Experiment completed with best_time: {best_time} median_time: {meadian_time} and mean time: {mean_time}. The success rate was: {success_rate}. Parameters: algo: {planner_algo}, max_vel: {max_vel}, max_acc: {max_acc}, checkpoint_offset: {checkpoint_offset}  can_pass_gate: {can_pass_gate}")

    return meadian_time


if __name__ == "__main__":

    log_path = "temp/hp_search.log"
    file_handler = logging.FileHandler(log_path, mode="w")
    console_handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    sampler = optuna.samplers.RandomSampler()
    study = optuna.create_study(direction="minimize", sampler=sampler)
    study.optimize(objective, n_trials=250)
    logger.info(f"BEst value is {study.best_value}")
    logger.info(f"Best params are {study.best_params}")

    
