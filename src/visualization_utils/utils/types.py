import numpy as np

from src.visualization_utils.utils.config_reader import ConfigReader
    
class Gate:
    def __init__(self, pos: np.ndarray, rot: np.ndarray, type):
        self.pos = pos
        self.rot = rot
        self.gate_type = type
    
    @staticmethod
    def from_nomial_gate_pos_and_type(gate_pos_and_type: np.ndarray):
        pos = np.array(gate_pos_and_type[:3])
        pos[2] = 0
        rot = np.array(gate_pos_and_type[3:6])
        type = int(gate_pos_and_type[6])
        return Gate(pos, rot, type)

    @staticmethod
    def from_within_flight_observation(gate_pose:np.ndarray, gate_type, within_range: bool):
        """
        Important! Durign flight, we receive the center point of the goal as reference coordinates ,this is different,
        than the initial nominal oversvation, where z is the lowest point of the gate. We must therefore subtract the gate height
        """
        pos = np.array(gate_pose[:3])
        if within_range:
            config_reader = ConfigReader.get()
            gate_properties = config_reader.get_gate_properties_by_type(gate_type)
            pos[2] -= gate_properties["height"]
        rot = np.array(gate_pose[3:6])
        return Gate(pos, rot, gate_type)

class Obstacle:
    def __init__(self, pos, rot):
        self.pos = pos
        self.rot = rot

    @staticmethod
    def from_obstacle_pos(obstacle_pos: np.ndarray):
        pos = np.array(obstacle_pos[:3])
        rot = np.array(obstacle_pos[3:6])
        return Obstacle(pos, rot)
