import os
import sys
from pathlib import Path
from typing import Callable, Optional, Tuple, Union


if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    raise ImportError("Please declare the environment variable 'SUMO_HOME'")
    
import gymnasium as gym
import numpy as np
import pandas as pd
import sumolib
import traci

from .traffic_signal import TrafficSignal


LIBSUMO = "LIBSUMO_AS_TRACI" in os.environ



class SumoEnvironment(gym.Env):

    metadata = {
        "render_modes": ["human", "rgb_array"],
    }

    CONNECTION_LABEL = 0  # For traci multi-client support

    def __init__(
        self,
        sumoconfig_file: str,
        out_csv_name: Optional[str] = None,
        use_gui: bool = False,
        virtual_display: Tuple[int, int] = (3200, 1800),
        begin_time: int = 0,
        num_seconds: int = 41000,
        max_depart_delay: int = -1,
        waiting_time_memory: int = 1000,
        time_to_teleport: int = -1,
        delta_time: int = 5,
        yellow_time: int = 2,
        min_green: int = 5,
        max_green: int = 60,
        add_system_info: bool = True,
        add_agent_info: bool = True,
        sumo_seed: Union[str, int] = "random",
        fixed_ts: bool = False,
        additional_sumo_cmd: Optional[str] = None,
        render_mode: Optional[str] = None,
    ) -> None:
        """Initialize the environment."""
        assert render_mode is None or render_mode in self.metadata["render_modes"], "Invalid render mode."
        self.render_mode = render_mode
        self.virtual_display = virtual_display
        self.disp = None

        self._conf = sumoconfig_file
        self.use_gui = use_gui
        if self.use_gui or self.render_mode is not None:
            self._sumo_binary = sumolib.checkBinary("sumo-gui")
        else:
            self._sumo_binary = sumolib.checkBinary("sumo")

        assert delta_time > yellow_time, "Time between actions must be at least greater than yellow time."

        self.begin_time = begin_time
        self.sim_max_time = begin_time + num_seconds
        self.delta_time = delta_time  # seconds on sumo at each step
        self.max_depart_delay = max_depart_delay  # Max wait time to insert a vehicle
        self.waiting_time_memory = waiting_time_memory  # Number of seconds to remember the waiting time of a vehicle (see https://sumo.dlr.de/pydoc/traci._vehicle.html#VehicleDomain-getAccumulatedWaitingTime)
        self.time_to_teleport = time_to_teleport
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_time = yellow_time
        self.sumo_seed = sumo_seed
        self.fixed_ts = fixed_ts
        self.additional_sumo_cmd = additional_sumo_cmd
        self.add_system_info = add_system_info
        self.add_agent_info = add_agent_info
        self.label = str(SumoEnvironment.CONNECTION_LABEL)
        SumoEnvironment.CONNECTION_LABEL += 1
        self.sumo = None

        if LIBSUMO:
            traci.start([sumolib.checkBinary("sumo"), "-c", self._conf])  # Start only to retrieve traffic light information
            conn = traci
        else:
            traci.start([sumolib.checkBinary("sumo"), "-c", self._conf], label="init_connection" + self.label)
            conn = traci.getConnection("init_connection" + self.label)

        self.ts_ids = list(conn.trafficlight.getIDList())
        self.ts_id = self.ts_ids[0]

        self.traffic_signal = TrafficSignal(
                self,
                self.ts_id,
                self.delta_time,
                self.yellow_time,
                self.min_green,
                self.max_green,
                self.begin_time,
                conn,
            )


        conn.close()

        self.vehicles = dict()
        self.total_waiting_time = 0
        self.total_co2_emission = 0
        self.total_fuel_consumption = 0
        self.seen_vehicles = set ()
        self.halted_vehicles = set()
        self.reward_range = (-float("inf"), float("inf"))
        self.episode = 0
        self.metrics = []
        self.out_csv_name = out_csv_name
        self.observation = None
        self.reward = 0.0
        
        self.fixed_ts_phase_id = 0

    def _start_simulation(self):
        sumo_cmd = [
            self._sumo_binary,
            "-c",
            self._conf,
            "--max-depart-delay",
            str(self.max_depart_delay),
            "--waiting-time-memory",
            str(self.waiting_time_memory),
            "--time-to-teleport",
            str(self.time_to_teleport),
        ]
        if self.begin_time > 0:
            sumo_cmd.append(f"-b {self.begin_time}")

        if self.sumo_seed == "random":
            sumo_cmd.append("--random")
        else:
            sumo_cmd.extend(["--seed", str(self.sumo_seed)])

        if self.additional_sumo_cmd is not None:
            sumo_cmd.extend(self.additional_sumo_cmd.split())

        if self.use_gui or self.render_mode is not None:
            sumo_cmd.extend(["--start", "--quit-on-end"])
            if self.render_mode == "rgb_array":
                sumo_cmd.extend(["--window-size", f"{self.virtual_display[0]},{self.virtual_display[1]}"])
                from pyvirtualdisplay.smartdisplay import SmartDisplay

                print("Creating a virtual display.")
                self.disp = SmartDisplay(size=self.virtual_display)
                self.disp.start()
                print("Virtual display started.")

        if LIBSUMO:
            traci.start(sumo_cmd)
            self.sumo = traci
        else:
            traci.start(sumo_cmd, label=self.label)
            self.sumo = traci.getConnection(self.label)

        if self.use_gui or self.render_mode is not None:
            self.sumo.gui.setSchema(traci.gui.DEFAULT_VIEW, "real world")

    def reset(self, seed: Optional[int] = None, **kwargs):
        """Reset the environment."""
        super().reset(seed=seed, **kwargs)

        if self.episode != 0:
            self.close()
            self.save_csv(self.out_csv_name, self.episode)
        self.episode += 1
        self.metrics = []

        if seed is not None:
            self.sumo_seed = seed
        self._start_simulation()

        self.traffic_signal = TrafficSignal(
                self,
                self.ts_id,
                self.delta_time,
                self.yellow_time,
                self.min_green,
                self.max_green,
                self.begin_time,
                self.sumo,
            )

        self.vehicles = dict()
        
        # print("+++++++++++++++++++++++= ", self.observation_space)
        # print("+++++++++++++++++++++++= ", self._compute_observation())
        # {'density':np.array([0,0,0,0], dtype=np.float32),'nb_veh':np.array([0,0,0,0], dtype=np.int32),'phase':np.array([0,0],dtype=np.int32)}

        return self._compute_observation(), self._compute_info()
    
    @property
    def sim_step(self) -> float:
        """Return current simulation second on SUMO."""
        return self.sumo.simulation.getTime()

    def step(self, action: int):
        """Apply the action(s) and then step the simulation for delta_time seconds.
        """
        # No action, follow fixed TL defined in self.phases
        if action is None:
            for _ in range(self.delta_time):
                self._sumo_step()
        # if self.fixed_ts:
        #     self.traffic_signal.sumo.trafficlight.setRedYellowGreenState(
        #             self.ts_id, self.traffic_signal.all_phases[self.fixed_ts_phase_id].state
        #         )
        #     self.fixed_ts_phase_id += 1
        #     if self.fixed_ts_phase_id:
        #         self.fixed_ts_phase_id = 0
                
        # print(f"+++++++++++++++++++ {self.fixed_ts_phase_id}")
                
        else:
            self._apply_action(action)
            self._run_steps()

        observation = self._compute_observation()
        reward = self._compute_reward()
        dones = self._compute_done()
        terminated = False  # there are no 'terminal' states in this environment
        truncated = dones["__all__"]  # episode ends when sim_step >= max_steps
        info = self._compute_info()

        return observation, reward, terminated, truncated, info
        # return np.array([45.0], dtype=np.float32), reward, done, info

    def _run_steps(self):
        time_to_act = False
        while not time_to_act:
            self._sumo_step()
            
            self.traffic_signal.update()
            if self.traffic_signal.time_to_act:
                time_to_act = True

    def _apply_action(self, action):
        """Set the next green phase for the traffic signals.

        Args:
            action: If single-agent, actions is an int between 0 and self.num_green_phases (next green phase)
        """
        
        # print("can act ? ",self.traffic_signal.time_to_act)
        if self.traffic_signal.time_to_act:
            self.traffic_signal.old_phase = self.traffic_signal.green_phase
            # print("can act ? ",self.traffic_signal.time_to_act)
            self.traffic_signal.set_next_phase(action)
            
                    
    def _compute_done(self):
        dones = {self.ts_id: False}
        dones["__all__"] = self.sim_step >= self.sim_max_time
        return dones

    def _compute_info(self):
        info = {"step": self.sim_step}
        # if self.add_system_info:
        #     info.update(self._get_system_info())
        if self.add_agent_info:
            info.update(self._get_agent_info())
        self.metrics.append(info.copy())
        return info

    def _compute_observation(self):
        
        # print("time to act : ", self.traffic_signal.time_to_act)
        if self.traffic_signal.time_to_act:
            self.observation = self.traffic_signal.compute_observation()
            #return self.observation.copy()
            
        # print("+++++++++++++++++++++++++++++++++++ === ",self.observation)
            # print("____________________________________=+ ",self.traffic_signal.get_vehicles_count_per_lane())
            # print("____________________________________=+ ",self.observation)
            return self.observation

    def _compute_reward(self):
        if self.traffic_signal.time_to_act:
            # print(f" next time to act {self.traffic_signal.next_action_time}")
            # print("")
            self.reward = self.traffic_signal.compute_reward() 
            return self.reward

    @property
    def observation_space(self):
        """Return the observation space of a traffic signal.

        Only used in case of single-agent environment.
        """
        return self.traffic_signal.observation_space

    @property
    def action_space(self):
        """Return the action space of a traffic signal.

        Only used in case of single-agent environment.
        """
        return self.traffic_signal.action_space

    def _sumo_step(self):
        self.sumo.simulationStep()

    def _get_system_info(self):
        vehicles = self.sumo.vehicle.getIDList()
        speeds = [self.sumo.vehicle.getSpeed(vehicle) for vehicle in vehicles]
        waiting_times = [self.sumo.vehicle.getWaitingTime(vehicle) for vehicle in vehicles]
        return {
            # In SUMO, a vehicle is considered halting if its speed is below 0.1 m/s
            "system_total_stopped": sum(int(speed < 0.1) for speed in speeds),
            "system_total_waiting_time": sum(waiting_times),
            "system_mean_waiting_time": 0.0 if len(vehicles) == 0 else np.mean(waiting_times),
            "system_mean_speed": 0.0 if len(vehicles) == 0 else np.mean(speeds),
        }



    def _get_agent_info(self):
        
        # acc, fuel, co2 = self.traffic_signal.get_stats()
        
        # accumulated_waiting_time = [
        #     sum(acc)
        # ]
        
        # fuel_consumption = [
        #     0
        # ]
        
        # co2_emission = [
        #     0
        # ]
        
        # total_vehicles_passed = [
        #     len(self.vehicles)
        # ]
        # average_speed = [self.traffic_signals[ts].get_average_speed() for ts in self.ts_ids]

        lane_temp = ["n_t_0", "n_t_1", "s_t_0", "s_t_1","w_t_0", "w_t_1", "e_t_0", "e_t_1"]
        co2, time, fuel = self.traffic_signal.get_vehicle_metrics_on_lanes(lane_temp)
        # stopped = [self.traffic_signal.get_total_queued(lane_temp)]
        # self.total_stopped += sum(stopped)

        # print("+++++++++++++++ AGENT Total Stoped : ", self.total_stopped)
        
        info = {}
        # for i, ts in enumerate(self.ts_ids):
        #     info[f"{ts}_stopped"] = stopped[i]
        #     info[f"{ts}_accumulated_waiting_time"] = accumulated_waiting_time[i]
        #     info[f"{ts}_average_speed"] = average_speed[i]
        # info["agent_total_stopped"] = sum(stopped)
        # info["agents_total_accumulated_waiting_time"] = sum(accumulated_waiting_time)
        
        info["agent_total_vehicles_passed"] = [len(self.seen_vehicles)]
        info["agent_total_stopped"] = [len(self.halted_vehicles)]
        info["agent_total_fuel_consumption"] = [self.total_fuel_consumption]
        info["agent_co2_emission"] = [self.total_co2_emission]
        info["agent_accumulated_waiting_time"] = [self.total_waiting_time]
        return info



    def close(self):
        """Close the environment and stop the SUMO simulation."""
        if self.sumo is None:
            return

        if not LIBSUMO:
            traci.switch(self.label)
        traci.close()

        if self.disp is not None:
            self.disp.stop()
            self.disp = None

        self.sumo = None

    def __del__(self):
        """Close the environment and stop the SUMO simulation."""
        self.close()

    def render(self):
        """Render the environment.

        If render_mode is "human", the environment will be rendered in a GUI window using pyvirtualdisplay.
        """
        if self.render_mode == "human":
            return  # sumo-gui will already be rendering the frame
        elif self.render_mode == "rgb_array":
            # img = self.sumo.gui.screenshot(traci.gui.DEFAULT_VIEW,
            #                          f"temp/img{self.sim_step}.jpg",
            #                          width=self.virtual_display[0],
            #                          height=self.virtual_display[1])
            img = self.disp.grab()
            return np.array(img)


    def save_csv(self, out_csv_name, episode):
        """Save metrics of the simulation to a .csv file.

        Args:
            out_csv_name (str): Path to the output .csv file. E.g.: "results/my_results
            episode (int): Episode number to be appended to the output file name.
        """
        if out_csv_name is not None:
            df = pd.DataFrame(self.metrics)
            Path(Path(out_csv_name).parent).mkdir(parents=True, exist_ok=True)
            df.to_csv(out_csv_name + f"_conn{self.label}_ep{episode}" + ".csv", index=False)
            
    