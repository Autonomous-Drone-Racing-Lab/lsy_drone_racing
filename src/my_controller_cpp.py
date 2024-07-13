from __future__ import annotations
import yaml
import numpy as np

from lsy_drone_racing.command import Command
from lsy_drone_racing.controller import BaseController
from lsy_drone_racing.utils import draw_traj_without_ref, remove_trajectory
from online_traj_planner import OnlineTrajGenerator # c++ binding
from enum import Enum

class QuadrotorState(Enum):
    INITIAL = 0
    TAKEOFF = 1
    FLYING = 2
    LANDING = 3
    LANDED = 4


class Controller(BaseController):
    """Template controller class."""

    def __init__(
        self,
        initial_obs: np.ndarray,
        initial_info: dict,
        buffer_size: int = 100,
        verbose: bool = False,
       # config = "./config.yaml"
       config = "hp_base_config_optimal.yaml",
       #config = "test_config.yaml"
       experiment_tracker = None
    ):
        """Initialization of the controller.

        Args:
            initial_obs: The initial observation of the quadrotor's state
                [x, x_dot, y, y_dot, z, z_dot, phi, theta, psi, p, q, r].
            initial_info: The a priori information as a dictionary with keys 'symbolic_model',
                'nominal_physical_parameters', 'nominal_gates_pos_and_type', etc.
            buffer_size: Size of the data buffers used in method `learn()`.
            verbose: Turn on and off additional printouts and plots.
            config: Path to the configuration file.
            experiment_tracker: Optional experiment tracker object to provide for collecting results over many runs
        """
        super().__init__(initial_obs, initial_info, buffer_size, verbose)

        # load config
        self.config_path = config
        with open(self.config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.takeoff_height = self.config["general_properties"]["takeoff_height"]
        self.takeoff_time = self.config["general_properties"]["takeoff_time"]
        self.traj_calc_duration = 0.02

        # Save environment and control parameters.
        self.initial_info = initial_info
        self.CTRL_TIMESTEP = initial_info["ctrl_timestep"]
        self.CTRL_FREQ = initial_info["ctrl_freq"]
        self.initial_obs = initial_obs
        self.VERBOSE = verbose
        self.VERBOSE = True
        self.BUFFER_SIZE = buffer_size
        self.quadrotor_state = QuadrotorState.INITIAL
        

        # Store a priori scenario information.
        self.NOMINAL_GATES = initial_info["nominal_gates_pos_and_type"]
        self.NOMINAL_OBSTACLES = initial_info["nominal_obstacles_pos"]
        self.GATE_TYPES = initial_info["gate_dimensions"]
        self.start_point = np.array([initial_obs[0], initial_obs[2], self.takeoff_height])
        self.goal_point = np.array([0, -2, 0.5]) # Hardcoded from the config file

        # Store Information for tracking
        self.gate_update_info = {}
        self.obstacle_update_info = {}

        # Setup the trajectory generator
        self.traj_generator_cpp = OnlineTrajGenerator(self.start_point, self.goal_point, self.NOMINAL_GATES, self.NOMINAL_OBSTACLES, self.config_path)
        self.traj_generator_cpp.pre_compute_traj(self.takeoff_time)

        if self.VERBOSE:
            traj = self.traj_generator_cpp.get_planned_traj()
            traj_positions = traj[:, [0, 3, 6]]
            draw_traj_without_ref(initial_info, traj_positions)
        
        self.experiment_tracker = experiment_tracker

        # For visualizing and tracking gate changes
        self.last_traj_recalc_time = None
        self.last_gate_change_time = 0
        self.last_gate_id = 0

        # Reset counters and buffers.
        self.reset()
        self.episode_reset()


    def compute_control(
        self,
        ep_time: float,
        obs: np.ndarray,
        reward: float | None = None,
        done: bool | None = None,
        info: dict | None = None,
    ) -> tuple[Command, list]:
        """Pick command sent to the quadrotor through a Crazyswarm/Crazyradio-like interface.

        Args:
            ep_time: Episode's elapsed time, in seconds.
            obs: The quadrotor's Vicon data [x, 0, y, 0, z, 0, phi, theta, psi, 0, 0, 0].
            reward: The reward signal.
            done: Wether the episode has terminated.
            info: Current step information as a dictionary with keys 'constraint_violation',
                'current_target_gate_pos', etc.

        Returns:
            The command type and arguments to be sent to the quadrotor. See `Command`.
        """
        
        current_drone_pos = np.array([obs[0], obs[2], obs[4]])
        current_target_gate_pos = info.get("current_target_gate_pos", None)
        current_target_gate_id = info.get("current_target_gate_id", None)
        current_target_gate_in_range = info.get("current_target_gate_in_range", None)

        if self.experiment_tracker is not None:
            self.experiment_tracker.add_drone_obs(current_drone_pos, ep_time)

        if not(current_target_gate_pos != None and current_target_gate_id != None and current_target_gate_in_range != None):
            pass
        else:
            # Normalizing such that all obstacles are always grounded
            current_target_gate_pos[2] = 0
            
            # Identify gate passed
            if current_target_gate_id != self.last_gate_id:
                self.last_gate_id = current_target_gate_id
                self.last_gate_change_time = ep_time
                # self.experiment_tracker.add_gate_passed()
            
            no_recompute = self.config["general_properties"].get("no_recompute", False)
            if not no_recompute:
                pos_updated = self.traj_generator_cpp.update_gate_pos(current_target_gate_id, current_target_gate_pos, current_drone_pos, current_target_gate_in_range, ep_time)
                if pos_updated: # for plotting
                    self.last_traj_recalc_time = ep_time
        
        # Plot trajectory after recomputation and some time
        if self.VERBOSE and self.last_traj_recalc_time and ep_time - self.last_traj_recalc_time > self.traj_calc_duration:
            remove_trajectory()
            traj = self.traj_generator_cpp.get_planned_traj()
            traj_positions = traj[:, [0, 3, 6]]
            draw_traj_without_ref(self.initial_info, traj_positions)
            self.last_traj_recalc_time = None

        # Calculate compute command based on current flight state
        if self.quadrotor_state == QuadrotorState.INITIAL:
            command_type = Command.TAKEOFF
            args = [self.takeoff_height, self.takeoff_time]
            self.quadrotor_state = QuadrotorState.TAKEOFF
        elif self.quadrotor_state == QuadrotorState.TAKEOFF:
            command_type = Command.NONE
            args = []
            if ep_time > self.takeoff_time:
                self.quadrotor_state = QuadrotorState.FLYING
        elif self.quadrotor_state == QuadrotorState.FLYING:
            traj_end_time = self.traj_generator_cpp.get_traj_end_time()
            traj_has_ended = ep_time > traj_end_time

            if traj_has_ended:
                command_type = Command.NOTIFYSETPOINTSTOP
                args = []
                self.quadrotor_state = QuadrotorState.LANDING
            else:
                traj_sample = self.traj_generator_cpp.sample_traj(ep_time)
                desired_pos = np.array([traj_sample[0], traj_sample[3], traj_sample[6]])
                desired_vel = np.array([traj_sample[1], traj_sample[4], traj_sample[7]])
                desired_acc = np.array([traj_sample[2], traj_sample[5], traj_sample[8]])
                use_yaw = self.config["general_properties"].get("use_yaw", False)
                if use_yaw:
                    yaw = traj_sample[9] if len(traj_sample) == 11 else 0
                else:
                    yaw = 0
                command_type = Command.FULLSTATE
                target_rpy_rates = np.zeros(3)
                args = [desired_pos, desired_vel, desired_acc, yaw, target_rpy_rates, ep_time]
        elif self.quadrotor_state == QuadrotorState.LANDING:
            command_type = Command.LAND
            args = [0.0, 2.0]
            self.quadrotor_state = QuadrotorState.LANDED
        elif self.quadrotor_state == QuadrotorState.LANDED:
            command_type = Command.FINISHED
            args = []
        else:
            print("Invalid state")
            exit(1)

        return command_type, args

    def step_learn(
        self,
        action: list,
        obs: np.ndarray,
        reward: float | None = None,
        done: bool | None = None,
        info: dict | None = None,
    ):
        """Learning and controller updates called between control steps.

        INSTRUCTIONS:
            Use the historically collected information in the five data buffers of actions,
            observations, rewards, done flags, and information dictionaries to learn, adapt, and/or
            re-plan.

        Args:
            action: Most recent applied action.
            obs: Most recent observation of the quadrotor state.
            reward: Most recent reward.
            done: Most recent done flag.
            info: Most recent information dictionary.

        """
        pass

        


    def episode_learn(self):
        """Learning and controller updates called between episodes.

        INSTRUCTIONS:
            Use the historically collected information in the five data buffers of actions,
            observations, rewards, done flags, and information dictionaries to learn, adapt, and/or
            re-plan.

        """
        #! Learning does hot happend because we are using either level0 or level3
        pass
        
      