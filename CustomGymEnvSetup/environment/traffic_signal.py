import os
import sys
from typing import Callable, List, Union, Tuple


if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    raise ImportError("Please declare the environment variable 'SUMO_HOME'")
import numpy as np
from gymnasium import spaces


class TrafficSignal:
    """This class represents a Traffic Signal controlling an intersection.

    It is responsible for retrieving information and changing the traffic phase using the Traci API.

    # Observation Space
    The default observation for each traffic signal agent is a vector:

    obs = [phase_one_hot, min_green, {'lane_id': density}, {'lane_id': nbVeh} ]

    - ```phase_one_hot``` is a one-hot encoded vector indicating the current active green phase
    - ```min_green``` is a binary variable indicating whether min_green seconds have already passed in the current phase

    # Action Space
    Action space is discrete, corresponding to put all into red, put the phase 1 into green and put the second phase into green

    0 : rrrrrrrrrrrrrrrr #all phase to red
    1 : GGGgrrrrGGGgrrrr #phase1 to green
    2 : rrrrGGGgrrrrGGGg #phase2 to green

    We have two phases (phase1 & phase2, each phase contain two values, 1st it green_phase, and it yellow phase (to 
    apply bfr switching)

    phases = {
        'phase1' : {
            'G' : 'GGGgrrrrGGGgrrrr',
            'y' : 'yyyyrrrryyyyrrrr'
        }

        'phase2' : {
            'G' : 'rrrrGGGgrrrrGGGg',
            'y' : 'rrrryyyyrrrryyyy'
        }
    }

    # Reward Function
    The default reward function is 'diff-waiting-time' principally

    but we have two other reward fonction

    1. if there is no vehicle in a phase, to the other put green, and keep red in da phase

        r1 = 5 else 0

    2. if there is no vehicle in all phase (phase1 & phase2) , select action_0, means put all TS into red light

        r2 = 7 else 0

    3. for the current phase

        if current phase in 'phases':

           { [ sum(wainting_time in his two lanes) - sum(of the waiting_time in the other phase) ] / 100 } -0.1

    4. Total reward

        reward = r1 + r2 + r3

    """

    # Default min gap of SUMO (see https://sumo.dlr.de/docs/Simulation/Safety.html). Should this be parameterized?
    MIN_GAP = 2.5

    def __init__(
        self,
        env,
        ts_id: str,
        delta_time: int,
        yellow_time: int,
        min_green: int,
        max_green: int,
        begin_time: int,
        sumo,
    ):
        self.id = ts_id
        self.env = env
        self.delta_time = delta_time
        self.yellow_time = yellow_time
        self.min_green = min_green
        self.max_green = max_green
        # self.is_all_red = 0
        self.green_phase = 1
        self.old_phase = None
        self.is_yellow = False
        self.time_since_last_phase_change = 0
        self.next_action_time = begin_time
        self.last_measure = 0.0
        self.last_density = 0.0
        # self.last_reward = None
        # self.reward_fn = reward_fn
        self.sumo = sumo

        self._build_phases()

        self.lanes = list(
            dict.fromkeys(self.sumo.trafficlight.getControlledLanes(self.id))
        )  # Remove duplicates and keep order
        self.out_lanes = [link[0][1] for link in self.sumo.trafficlight.getControlledLinks(self.id) if link]
        self.out_lanes = list(set(self.out_lanes))
        self.lanes_length = {lane: self.sumo.lane.getLength(lane) for lane in self.lanes + self.out_lanes}

        # set observation_space and action_space
        # self.observation_space = spaces.Box(low=0.0, high=np.inf, shape=(4,), dtype=np.float32)

        self.observation_space = spaces.Dict({
            'density': spaces.Box(low=np.array([0.0, 0.0, 0.0, 0.0]), high=np.array([20.0, 20.0, 20.0, 20.0]), shape=(4,), dtype=np.float64),  # Liste des densités dans chaque phase
            'nb_veh': spaces.Box(low=np.array([0, 0, 0, 0]), high=np.array([100, 100, 100, 100]), shape=(4,), dtype=np.int32),  # Liste des nombres de véhicules dans chaque voie
            'phase': spaces.Box(low=np.array([0,0]), high=np.array([1,1]), shape=(2,), dtype=np.int32),  # Liste des 2 phases
        })
        
        # self.observation_space = spaces.Box(low=np.array([25]), high=np.array([50]))

        self.action_space = spaces.Discrete(2)

    def _build_phases(self):
        phases = self.sumo.trafficlight.getAllProgramLogics(self.id)[0].phases
        self.all_phases = []

        self.num_green_phases = 2

        if self.env.fixed_ts:     
             pass

        self.green_phases = []
        # for the default phase
        # delay = 40
        # state ='rrrrrrrrrrrrrrrr'
        # self.green_phases.append(self.sumo.trafficlight.Phase(delay, state))
        delay = 40
        state = 'GGGgrrrrGGGgrrrr'
        self.green_phases.append(self.sumo.trafficlight.Phase(delay, state))
        delay = 40
        state = 'rrrrGGGgrrrrGGGg'
        self.green_phases.append(self.sumo.trafficlight.Phase(delay, state))

        self.yellow_dict = {}
        phase1=0
        yellow1_state = 'yyyyrrrryyyyrrrr'
        phase2=1
        yellow2_state = 'rrrryyyyrrrryyyy'
        self.yellow_dict = {
            # '1' : 0,
            phase1: yellow1_state,
            phase2: yellow2_state,
        }

        # for the first phase
        delay = 40
        state = 'GGGgrrrrGGGgrrrr'
        self.all_phases.append(self.sumo.trafficlight.Phase(delay, state))

        yellow_state = 'yyyyrrrryyyyrrrr'
        self.all_phases.append(self.sumo.trafficlight.Phase(self.yellow_time, yellow_state))

        # for the second phase
        delay = 40
        state = 'rrrrGGGgrrrrGGGg'
        self.all_phases.append(self.sumo.trafficlight.Phase(delay, state))

        yellow_state = 'rrrryyyyrrrryyyy'
        self.all_phases.append(self.sumo.trafficlight.Phase(self.yellow_time, yellow_state))

        programs = self.sumo.trafficlight.getAllProgramLogics(self.id)
        logic = programs[0]
        logic.type = 0
        logic.phases = self.all_phases
        self.sumo.trafficlight.setProgramLogic(self.id, logic)
        self.sumo.trafficlight.setRedYellowGreenState(self.id, self.all_phases[0].state)

    @property
    def time_to_act(self):
        """Returns True if the traffic signal should act in the current step."""
        return self.next_action_time == self.env.sim_step
    
    def update(self):
        """Updates the traffic signal state.

        If the traffic signal should act, it will set the next green phase and update the next action time.
        """
        self.time_since_last_phase_change += 1
        if self.is_yellow and self.time_since_last_phase_change == self.yellow_time:
            # self.sumo.trafficlight.setPhase(self.id, self.green_phase)
            self.sumo.trafficlight.setRedYellowGreenState(self.id, self.green_phases[self.green_phase].state)
            self.is_yellow = False

    def set_next_phase(self, new_phase: int):
        """Sets what will be the next green phase and sets yellow phase if the next phase is different than the current.

        Args:
            new_phase (int): Number between [0 ... num_green_phases]
        """
        # print("++++++ INFOS ++++++")
        # print(f"COUNTER : {self.time_since_last_phase_change} ")
        # print(f"min_green + yellow : {self.yellow_time + self.min_green} ")
        # print("")
        # print("QQQQQQQQQQQQQQQQQQQQQQQQQ Green_phases ",self.green_phases[0].state)
        # print("QQQQQQQQQQQQQQQQQQQQQQQQQ All_phases ",self.all_phases)
        new_phase = int(new_phase)
        # print("++++ Green Phase (2) : ", self.green_phase)
        # print("++++ New phase (2) : ", self.new_phase)
        if self.green_phase == new_phase or self.time_since_last_phase_change < self.yellow_time + self.min_green:
            # print("++++++ SAME ++++++")
            # print(f"Action : {new_phase} not perfomed")
            # print("new phases ",new_phase)
            # self.sumo.trafficlight.setPhase(self.id, self.green_phase)
            self.sumo.trafficlight.setRedYellowGreenState(self.id, self.green_phases[self.green_phase].state)
            self.next_action_time = self.env.sim_step + self.delta_time + self.yellow_time
        else:
            # print("++++++ NOW SWITCH ++++++")
            # self.sumo.trafficlight.setPhase(self.id, self.yellow_dict[(self.green_phase, new_phase)])  # turns yellow

            # # we check if the current phase is the 'rrrrrrrrrrrr' phase
            # # coz from this phase we don't want yellow before switching
            # if self.green_phase == 0:
            #     # print("++++++ DIFFERENT if zero ++++++")
            #     # print("green phases ",self.green_phase)
            #     # print("new phases ",new_phase)
            #     self.green_phase = new_phase
            #     # print("++++++ QQQQQQQ ++++++")
            #     # print("green phases ",self.green_phase)
            #     # print("new phases ",new_phase)
            #     self.next_action_time = self.env.sim_step + self.delta_time
            #     # self.is_yellow = True
            #     self.time_since_last_phase_change = 0
            # else:
            #     print("++++++ DIFFERENT else++++++")
            #     print("green phases ",self.green_phase)
            #     print("new phases ",new_phase)
            self.sumo.trafficlight.setRedYellowGreenState(
                self.id, self.yellow_dict[self.green_phase]
            )
            self.green_phase = new_phase
            self.next_action_time = self.env.sim_step + self.delta_time
            self.is_yellow = True
            self.time_since_last_phase_change = 0

    def compute_observation(self):
        """Computes the observation of the traffic signal."""
        """Return the default observation."""

        phase_id = [1 if self.green_phase == i else 0 for i in range(1, self.num_green_phases+1)]  # one-hot encoding
        min_green = [0 if self.time_since_last_phase_change < self.min_green + self.yellow_time else 1][0]
        density = self.get_lanes_density()
        nb_veh = self.get_vehicles_count_per_lane()
        # observation = np.array(phase_id + min_green + density + veh_nb, dtype=np.float32)
        
        observation = {
            'density': np.array(density, dtype=np.float64),
            'nb_veh': np.array(nb_veh, dtype=np.int32),
            'phase': np.array(phase_id, dtype=np.int32)
        }
        
        return observation

    # def get_lanes_density(self):
    #     """
    #     Retourne la densité dans chaque voie de l'intersection.

    #     Returns:
    #         dict: Un dictionnaire contenant l'ID de la voie comme clé et la densité de la voie comme valeur.
    #     """
    #     lanes_density = {}
    #     for lane in self.lanes:
    #         # lane_density = self.sumo.lane.getLastStepVehicleNumber(lane) / (self.lanes_length[lane] / (self.MIN_GAP + self.sumo.lane.getLastStepLength(lane)))
            
    #         lane_density = self.sumo.lane.getLastStepVehicleNumber(lane) / (self.lanes_length[lane] / (self.MIN_GAP + self.sumo.lane.getLastStepLength(lane)))
            
    #         lanes_density[lane] = min(1, lane_density)  # Limitation de la densité à 1
    #     return lanes_density
    
    # def get_vehicles_count_per_lane(self):
    #     """
    #     Retourne le nombre de véhicules dans chaque voie de l'intersection.

    #     Returns:
    #         dict: Un dictionnaire contenant l'ID de la voie comme clé et le nombre de véhicules dans la voie comme valeur.
    #     """
    #     vehicles_count_per_lane = {}
    #     for lane in self.lanes:
    #         vehicles_count = len(self.sumo.lane.getLastStepVehicleIDs(lane))
    #         vehicles_count_per_lane[lane] = vehicles_count
    #     return vehicles_count_per_lane
    
    def get_lanes_density(self) -> List[float]:
        """Returns the density [0,1] of the vehicles in the incoming lanes of the intersection.

        Obs: The density is computed as the number of vehicles divided by the number of vehicles that could fit in the lane.
        """
        lanes_density = [
            self.sumo.lane.getLastStepVehicleNumber(lane)
            / (self.lanes_length[lane] / (self.MIN_GAP + self.sumo.lane.getLastStepLength(lane)))
            for lane in self.lanes
        ]
        
        # print("--- Lanes density : ", lanes_density)
        
        new_list = []
        for i in range(0, len(lanes_density), 2):
            # Ajouter la somme des éléments consécutifs
            new_list.append((lanes_density[i] + lanes_density[i + 1]) / 2)
    
        return [min(1, density) for density in new_list]
    
    def get_phases_density(self, lanes_density: List[float]) -> List[float]:

        phases_density = []
        for i in range(0, len(lanes_density)-2):
            phases_density.append((lanes_density[i] + lanes_density[i+2]) / 2)
            
        return phases_density
    
    def get_vehicles_count_per_lane(self):
        """
        Retourne le nombre de véhicules dans chaque voie de l'intersection.

        Returns:
            dict: Un dictionnaire contenant l'ID de la voie comme clé et le nombre de véhicules dans la voie comme valeur.
        """
        vehicles_count_per_lane = [
            len(self.sumo.lane.getLastStepVehicleIDs(lane)) for lane in self.lanes
        ]
        
        new_list = []
        for i in range(0, len(vehicles_count_per_lane), 2):
            # Ajouter la somme des éléments consécutifs
            new_list.append(vehicles_count_per_lane[i] + vehicles_count_per_lane[i + 1])
            
        return new_list
    


    def compute_reward(self):
        """Computes the reward of the traffic signal."""
        self.last_reward = self.custom_reward()
        return self.last_reward

    def custom_reward(self):
        """
        Calcule la récompense basée sur plusieurs critères.

        Returns:
            float: La somme des trois récompenses.
        """
        # Récupérer le nombre de véhicules dans chaque voie de la phase 1
        phase1_top_lane_count_0 = len(self.sumo.lane.getLastStepVehicleIDs("n_t_0"))
        phase1_top_lane_count_1 = len(self.sumo.lane.getLastStepVehicleIDs("n_t_1"))
        phase1_top_lane_count = phase1_top_lane_count_0 + phase1_top_lane_count_1
        
        phase1_bottom_lane_count_0 = len(self.sumo.lane.getLastStepVehicleIDs("s_t_0"))
        phase1_bottom_lane_count_1 = len(self.sumo.lane.getLastStepVehicleIDs("s_t_1"))
        phase1_bottom_lane_count = phase1_bottom_lane_count_0 + phase1_bottom_lane_count_1

        # Récupérer le nombre de véhicules dans chaque voie de la phase 2
        phase2_left_lane_count_0 = len(self.sumo.lane.getLastStepVehicleIDs("w_t_0"))
        phase2_left_lane_count_1 = len(self.sumo.lane.getLastStepVehicleIDs("w_t_1"))
        phase2_left_lane_count = phase2_left_lane_count_0 + phase2_left_lane_count_1
        
        phase2_right_lane_count_0 = len(self.sumo.lane.getLastStepVehicleIDs("e_t_0"))
        phase2_right_lane_count_1 = len(self.sumo.lane.getLastStepVehicleIDs("e_t_1"))
        phase2_right_lane_count = phase2_right_lane_count_0 + phase2_right_lane_count_1

        # Calculer le nombre total de véhicules dans chaque phase
        phase1_total_count = phase1_top_lane_count + phase1_bottom_lane_count
        phase2_total_count = phase2_left_lane_count + phase2_right_lane_count
        phase1_total_count = int(phase1_total_count)
        phase2_total_count = int(phase2_total_count)

        # Initialiser les récompenses
        reward1 = 0
        reward2 = 0
        reward3 = 0
        reward4 = 0

        # Calculer la récompense 1
        if phase1_total_count == 0 and phase2_total_count != 0:
            if self.green_phase == 2:  # Si la phase 1 (voies du haut et du bas) est active
                reward1 = 10
            if self.green_phase == 1:  # Si la phase 1 (voies du haut et du bas) est active
                reward1 = -10
            if self.green_phase == 0:  # Si la phase 1 (voies du haut et du bas) est active
                reward1 = -10
                
        if phase2_total_count == 0 and phase1_total_count != 0:
            if self.green_phase == 2:  # Si la phase 2 (voies de gauche et de droite) est active
                reward1 = -10
            if self.green_phase == 1:
                reward1 = 10
            if self.green_phase == 0:  # Si la phase 1 (voies du haut et du bas) est active
                reward1 = -10

        # Calculer la récompense 2
        if phase1_total_count == 0 and phase2_total_count == 0:
            if self.green_phase == 0:  # Vérifier si tous les feux sont rouges
                reward2 = 15
            if self.green_phase == 1:  # Si la phase 1 (voies du haut et du bas) est active
                reward2 = -15
            if self.green_phase == 2:  # Si la phase 1 (voies du haut et du bas) est active
                reward2 = -15

        # Calculer la récompense 3
        phase1_waiting_time = sum(self.get_accumulated_waiting_time_per_lane(["n_t_0", "n_t_1", "s_t_0", "s_t_1"]))
        phase2_waiting_time = sum(self.get_accumulated_waiting_time_per_lane(["w_t_0", "w_t_1", "e_t_0", "e_t_1"]))

        if phase1_total_count != 0 and phase2_total_count != 0:
            if self.green_phase == 0:
                # reward3 = -((phase1_waiting_time + phase2_waiting_time) / 100.0) + 0.1
                reward3 = -15
            if self.green_phase == 1:
                reward3 = ((phase1_waiting_time - phase2_waiting_time) / 100.0) + 0.1
            if self.green_phase == 2:
                reward3 = ((phase2_waiting_time - phase1_waiting_time) / 100.0) + 0.1
                
        # Testing new reward for 3rd Trainning : 200k timestep
        # if phase2_total_count == 0 and phase1_total_count == 0:
        if self.green_phase == 0:
            reward4 = -((phase1_waiting_time + phase2_waiting_time) / 100.0) + 0.2
        if self.green_phase == 1:
            reward4 = ((phase1_waiting_time - phase2_waiting_time) / 100.0) + 0.1
        if self.green_phase == 2:
            reward4 = ((phase2_waiting_time - phase1_waiting_time) / 100.0) + 0.1

        # Retourner la somme des récompenses
        # print("reward a",reward1)
        # print("reward b",reward2)
        # print("reward c",reward3)
        # print("")
        # print("phase1 total count ",phase1_total_count)
        # print("phase2 total count ",phase2_total_count)
        # print("phase1 waiting time ",phase1_waiting_time)
        # print("phase2 waiting time ",phase2_waiting_time)
        # return reward1 + reward2 + reward3
        one_hot_wt = [phase1_waiting_time, phase2_waiting_time]
        # print("+++++++++ ONEHOTWAITING : ",one_hot_wt)
        
        
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #
        # REWARD3 WAITHING TIME : reward3 = last_density - density
        #
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        
        
        ts_wait = sum(self.get_accumulated_waiting_time_per_lane(["n_t_0", "n_t_1", 
                    "s_t_0", "s_t_1","w_t_0", "w_t_1", "e_t_0", "e_t_1"])) / 100.0
        reward3 = self.last_measure - ts_wait
        # print("++++ Last WT : ",self.last_measure)
        # print("++++ NEW WT : ",ts_wait)
        
        self.last_measure = ts_wait
        
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #
        # REWARD4 DIFF DENSITY : reward4 = self.last_density - density
        #
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        
        phases_density = self.get_phases_density(self.get_lanes_density())
        density_sum = sum(phases_density) / 2
        
        reward4 = self.last_density - density_sum
        
        print("++++ Phases density : ", phases_density)
        print("++++ Last Density : ",self.last_density)
        print("++++ NEW Density : ",density_sum)
        # print("++++ Green Phase (1) : ", self.green_phase)
        # print("++++ Old phase (1) : ", self.old_phase)
        # print("++++ Density : ", density)
        # print("++++ Lane : ", self.lanes)
        # print("++++ Out Lanes : ", self.out_lanes)
        # print("++++ Phases density : ", phases_density)
        self.last_density = density_sum
        
        # if self.green_phase == 0:
        #     if phase1_total_count == 0:
        #         reward4 -= 1
        #     else:
        #         reward4 += 1
                
        # if self.green_phase == 1:
        #     if phase2_total_count == 0:
        #         reward4 -= 1
        #     else:
        #         reward4 += 1
        
        # if self.old_phase != self.green_phase:
        #     if phadensity[self.old_phase] > 0.2:
        #         reward4 -= 1
        
        return reward4

    def get_accumulated_waiting_time_per_lane(self, lanes) -> List[float]:
        """
        Retourne le temps d'attente accumulé dans chaque voie spécifiée.

        Args:
            lanes (list): Liste des ID des voies pour lesquelles on veut récupérer le temps d'attente.

        Returns:
            list: Liste du temps d'attente accumulé dans chaque voie spécifiée.
        """
        wait_time_per_lane = []
        for lane in lanes:
            veh_list = self.sumo.lane.getLastStepVehicleIDs(lane)
            wait_time = 0.0
            for veh in veh_list:
                acc = self.sumo.vehicle.getAccumulatedWaitingTime(veh)
                wait_time += acc
            wait_time_per_lane.append(wait_time)
        return wait_time_per_lane
    
    def get_stats(self) -> List[float]:
        """Returns the accumulated waiting time, fuel consumption, co2 emmission per lane.

        Returns:
            List[float]: List of accumulated waiting time of each intersection lane.
        """
        wait_time_per_lane = []
        fuel_consumption_per_lane = []
        co2_emission_per_lane = []
        
        for lane in self.lanes:
            veh_list = self.sumo.lane.getLastStepVehicleIDs(lane)
            
            wait_time = 0.0
            fuel_consumption = 0
            co2_emission = 0
            
            for veh in veh_list:
                veh_lane = self.sumo.vehicle.getLaneID(veh)
                
                acc = self.sumo.vehicle.getAccumulatedWaitingTime(veh)
                fuel = self.sumo.vehicle.getFuelConsumption(veh)
                co2 = self.sumo.vehicle.getCO2Emission(veh)
                
                if veh not in self.env.vehicles:
                    self.env.vehicles[veh] = {veh_lane: acc}
                    self.env.total_waiting_time += acc
                else:
                    self.env.vehicles[veh][veh_lane] = acc - sum(
                        [self.env.vehicles[veh][lane] for lane in self.env.vehicles[veh].keys() if lane != veh_lane]
                    )
                    
                    
                    # self.env.vehicles[veh][veh_lane][1] = fuel - sum(
                    #     [self.env.vehicles[veh][lane][1] for lane in self.env.vehicles[veh].keys() if lane != veh_lane]
                    # )
                    
                    # self.env.vehicles[veh][veh_lane][2] = co2 - sum(
                    #     [self.env.vehicles[veh][lane][2] for lane in self.env.vehicles[veh].keys() if lane != veh_lane]
                    # )
                    
                wait_time += self.env.vehicles[veh][veh_lane]
                # fuel_consumption += self.env.vehicles[veh][veh_lane][1]
                # co2_emission += self.env.vehicles[veh][veh_lane][2]
                
            wait_time_per_lane.append(wait_time)
            # fuel_consumption_per_lane.append(fuel_consumption)
            # co2_emission_per_lane.append(co2_emission)
            
        return wait_time_per_lane, 0, 0
    
    def get_vehicle_metrics_on_lanes(self, lanes: List[str]) -> Tuple[float, float, float]:
        """Calculates the total CO2 emission, total waiting time, and total fuel consumption of vehicles on specified lanes.
        
        Args:
            lanes (List[str]): List of lane IDs.
        
        Returns:
            Tuple[float, float, float]: Total CO2 emission, total waiting time, and total fuel consumption of vehicles on specified lanes.
        """
        total_co2_emission = 0.0  # Initialize total CO2 emission to 0
        total_waiting_time = 0.0  # Initialize total waiting time to 0
        total_fuel_consumption = 0.0  # Initialize total fuel consumption to 0
        seen_vehicles = set()  # Set to store seen vehicles
        
        for lane in lanes:
            veh_list = self.sumo.lane.getLastStepVehicleIDs(lane)  # Get list of vehicles on lane
            for veh in veh_list:
                if veh not in self.env.seen_vehicles:  # Check if vehicle has not been seen before
                    co2_emission = self.sumo.vehicle.getCO2Emission(veh)  # Get CO2 emission of vehicle
                    waiting_time = self.sumo.vehicle.getAccumulatedWaitingTime(veh)  # Get waiting time of vehicle
                    fuel_consumption = self.sumo.vehicle.getFuelConsumption(veh)  # Get fuel consumption of vehicle
                    total_co2_emission += co2_emission  # Add CO2 emission to total
                    total_waiting_time += waiting_time  # Add waiting time to total
                    total_fuel_consumption += fuel_consumption  # Add fuel consumption to total
                    self.env.seen_vehicles.add(veh)  # Add vehicle to set of seen vehicles
                    
        self.env.total_fuel_consumption += total_fuel_consumption
        self.env.total_co2_emission += total_co2_emission
        self.env.total_waiting_time += total_waiting_time
        
        return total_co2_emission, total_waiting_time, total_fuel_consumption


    def get_average_speed(self) -> float:
        """Returns the average speed normalized by the maximum allowed speed of the vehicles in the intersection.

        Obs: If there are no vehicles in the intersection, it returns 1.0.
        """
        avg_speed = 0.0
        vehs = self._get_veh_list()
        if len(vehs) == 0:
            return 1.0
        for v in vehs:
            avg_speed += self.sumo.vehicle.getSpeed(v) / self.sumo.vehicle.getAllowedSpeed(v)
        return avg_speed / len(vehs)

    def _get_veh_list(self):
        veh_list = []
        for lane in self.lanes:
            veh_list += self.sumo.lane.getLastStepVehicleIDs(lane)
            
        new_list = []
        for i in range(0, len(veh_list), 2):
            # Ajouter la somme des éléments consécutifs
            new_list.append(veh_list[i] + veh_list[i + 1])
            
        return new_list


