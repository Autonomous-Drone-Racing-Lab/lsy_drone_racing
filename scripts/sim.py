"""Simulate the competition as in the IROS 2022 Safe Robot Learning competition.

Run as:

    $ python scripts/sim.py --config config/getting_started.yaml

Look for instructions in `README.md` and `edit_this.py`.
"""

from __future__ import annotations

import logging
import os

# Fix, so we can import form the src module
import sys
import time
from functools import partial
from pathlib import Path

import fire
import numpy as np
import pybullet as p
import yaml
from munch import Munch, munchify
from safe_control_gym.utils.registration import make
from safe_control_gym.utils.utils import sync

from lsy_drone_racing.command import apply_sim_command
from lsy_drone_racing.utils import load_controller

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.experiment_trakcer import ExperimentTracker

logger = logging.getLogger(__name__)


def simulate(
    config: str = "config/level3.yaml",
    controller: str = "src/my_controller_cpp.py",
    n_runs: int = 1,
    gui: bool = True,
    terminate_on_lap: bool = True,
    controller_config: str = "controller_config/hp_base_config_optimal.yaml"
) -> list[float]:
    """Evaluate the drone controller over multiple episodes.

    Args:
        config: The path to the configuration file.
        controller: The path to the controller module.
        n_runs: The number of episodes.
        gui: Enable/disable the simulation GUI.
        terminate_on_lap: Stop the simulation early when the drone has passed the last gate.
        controller_config: The path to the controller configuration

    Returns:
        A list of episode times.
    """
    # Load configuration and check if firmare should be used.
    path = Path(config)
    assert path.exists(), f"Configuration file not found: {path}"
    with open(path, "r") as file:
        config = munchify(yaml.safe_load(file))
    # Overwrite config options
    config.quadrotor_config.gui = gui
    CTRL_FREQ = config.quadrotor_config["ctrl_freq"]
    CTRL_DT = 1 / CTRL_FREQ

    # Create environment.
    assert config.use_firmware, "Firmware must be used for the competition."
    FIRMWARE_FREQ = 500
    pyb_freq = config.quadrotor_config["pyb_freq"]
    assert pyb_freq % FIRMWARE_FREQ == 0, "pyb_freq must be a multiple of firmware freq"
    # The env.step is called at a firmware_freq rate, but this is not as intuitive to the end
    # user, and so we abstract the difference. This allows ctrl_freq to be the rate at which the
    # user sends ctrl signals, not the firmware.
    config.quadrotor_config["ctrl_freq"] = FIRMWARE_FREQ
    env_func = partial(make, "quadrotor", **config.quadrotor_config)
    wrapped_env = make("firmware", env_func, FIRMWARE_FREQ, CTRL_FREQ)
    env = wrapped_env.env

    # Load the controller module
    path = Path(__file__).parents[1] / controller
    ctrl_class = load_controller(path)  # This returns a class, not an instance

    # Create a statistics collection
    stats = {
        "ep_reward": 0,
        "collisions": 0,
        "collision_objects": set(),
        "violations": 0,
        "gates_passed": 0,
    }
    ep_times = []

    experiment_tracker = ExperimentTracker()

    # Run the episodes.
    for i in range(n_runs):
        experiment_tracker.add_experiment()
        try:
            ep_start = time.time()
            done = False
            action = np.zeros(4)
            reward = 0
            obs, info = wrapped_env.reset()
            info["ctrl_timestep"] = CTRL_DT
            info["ctrl_freq"] = CTRL_FREQ
            lap_finished = False
            # obs = [x, x_dot, y, y_dot, z, z_dot, phi, theta, psi, p, q, r]
            vicon_obs = [obs[0], 0, obs[2], 0, obs[4], 0, obs[6], obs[7], obs[8], 0, 0, 0]
            
            if controller_config is None:
                ctrl = ctrl_class(vicon_obs, info, verbose=config.verbose)
            else:
                ctrl = ctrl_class(vicon_obs, info, verbose=config.verbose, config=controller_config, experiment_tracker=experiment_tracker)

            gui_timer = p.addUserDebugText("", textPosition=[0, 0, 1], physicsClientId=env.PYB_CLIENT)
            i = 0
            while not done:
                curr_time = i * CTRL_DT
                gui_timer = p.addUserDebugText(
                    "Ep. time: {:.2f}s".format(curr_time),
                    textPosition=[0, 0, 1.5],
                    textColorRGB=[1, 0, 0],
                    lifeTime=3 * CTRL_DT,
                    textSize=1.5,
                    parentObjectUniqueId=0,
                    parentLinkIndex=-1,
                    replaceItemUniqueId=gui_timer,
                    physicsClientId=env.PYB_CLIENT,
                )

                # Get the observation from the motion capture system
                vicon_obs = [obs[0], 0, obs[2], 0, obs[4], 0, obs[6], obs[7], obs[8], 0, 0, 0]
                # Compute control input.
                command_type, args = ctrl.compute_control(curr_time, vicon_obs, reward, done, info)
                # Apply the control input to the drone. This is a deviation from the gym API as the
                # action is not applied in env.step()
                apply_sim_command(wrapped_env, command_type, args)
                obs, reward, done, info, action = wrapped_env.step(curr_time, action)
                # Update the controller internal state and models.
                ctrl.step_learn(action, obs, reward, done, info)
                # Add up reward, collisions, violations.
                stats["ep_reward"] += reward
                if info["collision"][1]:
                    stats["collisions"] += 1
                    stats["collision_objects"].add(info["collision"][0])
                stats["violations"] += "constraint_violation" in info and info["constraint_violation"]

                # Synchronize the GUI.
                if config.quadrotor_config.gui:
                    sync(i, ep_start, CTRL_DT)
                i += 1
                # Break early after passing the last gate (=> gate -1) or task completion
                if terminate_on_lap and info["current_target_gate_id"] == -1:
                    info["task_completed"], lap_finished = True, True
                if info["task_completed"]:
                    done = True

            # Learn after the episode if the controller supports it
            ctrl.episode_learn()  # Update the controller internal state and models.
            log_episode_stats(stats, info, config, curr_time, lap_finished)
            ctrl.episode_reset()
            # Reset the statistics
            stats["ep_reward"] = 0
            stats["collisions"] = 0
            stats["collision_objects"] = set()
            stats["violations"] = 0
            ep_times.append(curr_time if info["current_target_gate_id"] == -1 else None)
        
        # cath keyboad interup
        except KeyboardInterrupt:
            print("Keyboard interrupt. Exiting.")
            exit(0)
        except Exception as e:
            print(f"Error during episode {i}. The error was: {e}. Skipping to next episode.")

    # Close the environment
    env.close()

    out_path = "experiments.pkl"
    experiment_tracker.save_experiment(out_path)
    return ep_times


def log_episode_stats(stats: dict, info: dict, config: Munch, curr_time: float, lap_finished: bool):
    gates = [6, 7, 8, 9]
    obstacles = [3,2,5,4]

    def get_name(collision_info):
        id, did_collide = collision_info
        if not did_collide:
            return "collision_free"
        if id is None:
            return "world"
        
        if id in gates:
            idx = gates.index(id)
            return f"gate_{idx}"
        if id in obstacles:
            idx = obstacles.index(id)
            return f"obstacle_{idx}"
        
        return f"unknown_{id}"

    """Log the statistics of a single episode."""
    stats["gates_passed"] = info["current_target_gate_id"]
    if stats["gates_passed"] == -1:  # The drone has passed the final gate
        stats["gates_passed"] = len(config.quadrotor_config.gates)
    if config.quadrotor_config.done_on_collision and info["collision"][1]:
        termination = "COLLISION"
    elif config.quadrotor_config.done_on_completion and info["task_completed"] or lap_finished:
        termination = "TASK COMPLETION"
    elif config.quadrotor_config.done_on_violation and info["constraint_violation"]:
        termination = "CONSTRAINT VIOLATION"
    else:
        termination = "MAX EPISODE DURATION"
    logger.info(
        (
            f"Flight time (s): {curr_time}\n"
            f"Reason for termination: {termination}\n"
            f"Collision info: {get_name(info['collision'])}\n"
            f"Gates passed: {stats['gates_passed']}\n"
            f"Total reward: {stats['ep_reward']}\n"
            f"Number of collisions: {stats['collisions']}\n"
            f"Number of constraint violations: {stats['violations']}\n"
        )
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fire.Fire(simulate)
