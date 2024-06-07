import gymnasium as gym
from CustomGymEnvSetup import *
import os
from stable_baselines3 import PPO
from stable_baselines3.dqn.dqn import DQN

env = gym.make('instigo-goma-rl-v0',
                sumoconfig_file="E:\Instigo-TS-CTRL\\network_trainning\single-intersection-new.sumocfg",
                use_gui=True,
                num_seconds=41000,
              )

obs, info = env.reset()

for i in range(100000):
    action = env.action_space.sample()  # agent policy that uses the observation and info
    #obs, rewards, terminated, truncated, info = vec_env.step(action)
    obs, reward, terminated, truncated, info = env.step(action)
    
    print(f" Action : ", action)
    #print(f" Obs : ", obs)
    print(f" Reward : ", reward)
    print(f" Obs : ", obs['nb_veh'])
    print(f" ")
    # # print(f" Observation : ", obs)
    print(f" Info : ", info)