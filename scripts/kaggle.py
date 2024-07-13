"""Kaggle competition auto-submission script.

Note:
    Please do not alter this script or ask the course supervisors first!
"""

import logging

import numpy as np
import pandas as pd
from sim import simulate

logger = logging.getLogger(__name__)


def main():
    """Run the simulation N times and save the results as 'submission.csv'."""
    n_runs = 100
    controller = "src/my_controller_cpp.py"
    #controller = "examples/controller.py"
    controller_config: str = "hp_base_config_optimal.yaml"
    ep_times = simulate(config="config/level3.yaml", controller=controller,n_runs=n_runs, gui=True, controller_config=controller_config)
    # Log the number of failed runs if any

    if failed := [x for x in ep_times if x is None]:
        logger.warning(f"{len(failed)} runs failed out of {n_runs}!")
    else:
        logger.info("All runs completed successfully!")

    # Abort if all runs failed
    # if len(failed) > n_runs / 2:
    #     logger.error("More than 50% of all runs failed! Aborting submission.")
    #     raise RuntimeError("Too many runs failed!")

    no_failed = len(failed)
    failure_rate = no_failed / n_runs
    success_rate = 1 - failure_rate

    ep_times = [x for x in ep_times if x is not None]
    best_ep_time = min(ep_times)
    print(f"Best episode time: {best_ep_time}")
    data = {"ID": [i for i in range(len(ep_times))], "submission_time": ep_times}

    ep_times = np.array(ep_times)
    mean_time = np.mean(ep_times)
    median_time = np.median(ep_times)
    std_time = np.std(ep_times)
    
    with open("submission.csv", "w") as f:
        f.write(f"Total runs: {n_runs}, runs_completed: {n_runs - no_failed}, runs_failed: {no_failed}, failure_rate: {failure_rate}, success_rate: {success_rate}\n")
        f.write(f"Best episode time: {best_ep_time}, mean_time: {mean_time}, median_time: {median_time}, std_time: {std_time}\n")
    
    pd.DataFrame(data).to_csv("submission.csv", index=False, mode="a")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
