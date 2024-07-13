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


def create_config(config_path, temp_dir, max_time):
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    temp_path = os.path.join(temp_dir, "config_spline.yaml")
    
    config["trajectory_generator_properties"]["max_time"] = max_time

    with open(temp_path, "w") as file:
        yaml.dump(config, file)
    
    return temp_path



# def objective(trial):
#     CONFIG_PATH = "./hp_base_config_spline.yaml"
#     TEMP_DIR = "./temp"
#     controller = "src/my_controller_cpp.py"
#     task_config = "config/level3.yaml"
#     N_RUNS = 20

#     planner_algo = "fmt" # trial.suggest_categorical("planner_algo", ["rrt", "fmt"])
#     max_time = trial.suggest_float("max_time", 12, 18)
#     checkpoint_offset = 0.1 # trial.suggest_float("checkpoint_offset", 0.05, 0.15)
#     controller_config = create_config(CONFIG_PATH, TEMP_DIR, planner_algo, max_time, checkpoint_offset)

#     ep_times = simulate(config=task_config, controller=controller, n_runs=N_RUNS, gui=False, controller_config=controller_config)
#     # mark this trial as failed
#     failed_runs = len([x for x in ep_times if x is None])
#     success_rate = (N_RUNS - failed_runs) / N_RUNS    
#     ep_times = np.array([x for x in ep_times if x is not None])
#     if len(ep_times) == 0:
#         logger.info(f"Experiment failed all runs. Params: algo: {planner_algo}, max_time: {max_time} checkpoint_offset: {checkpoint_offset}  can_pass_gate: {can_pass_gate}")
#         return None
#     # find median time
#     best_time = np.min(ep_times)
#     meadian_time = np.median(ep_times)
#     mean_time = np.mean(ep_times)
    
#     logger.info(f"Experiment completed with best_time: {best_time} median_time: {meadian_time} and mean time: {mean_time}. The success rate was: {success_rate}. Parameters: algo: {planner_algo}, max_time: {max_time}, checkpoint_offset: {checkpoint_offset}  can_pass_gate: {can_pass_gate}")

#     return meadian_time

def objective(idx, n_runs):
    CONFIG_PATH = "./hp_base_config_spline.yaml"
    TEMP_DIR = "./temp"
    controller = "src/my_controller_cpp.py"
    task_config = "config/level1.yaml"
    N_RUNS = 20

    # planner_algo = "fmt" # trial.suggest_categorical("planner_algo", ["rrt", "fmt"])
    # max_time = trial.suggest_float("max_time", 12, 18)
    # checkpoint_offset = 0.1 # trial.suggest_float("checkpoint_offset", 0.05, 0.15)
    min_time = 10
    max_time = 12
    time = min_time + (max_time - min_time) * idx / n_runs
    print(f"Starting new experiment with {time}")
    controller_config = create_config(CONFIG_PATH, TEMP_DIR, max_time=time)

    ep_times = simulate(config=task_config, controller=controller, n_runs=N_RUNS, gui=False, controller_config=controller_config)
    # mark this trial as failed
    failed_runs = len([x for x in ep_times if x is None])
    success_rate = (N_RUNS - failed_runs) / N_RUNS    
    ep_times = np.array([x for x in ep_times if x is not None])
    if len(ep_times) == 0:
        logger.info(f"Experiment failed all runs. Params: a max_time: {time}")
        return None
    # find median time
    best_time = np.min(ep_times)
    meadian_time = np.median(ep_times)
    mean_time = np.mean(ep_times)
    
    logger.info(f"Experiment completed with best_time: {best_time} median_time: {meadian_time} and mean time: {mean_time}. The success rate was: {success_rate}. max_time: {time}")

    return meadian_time

if __name__ == "__main__":

    log_path = "temp/hp_search_spline.log"
    file_handler = logging.FileHandler(log_path, mode="w")
    console_handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    n_trials = 10
    for i in range(n_trials):
        objective(i, n_trials)

    
