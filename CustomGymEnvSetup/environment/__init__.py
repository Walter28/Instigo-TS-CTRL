"""SUMO Environment for Traffic Signal Control."""

from gymnasium.envs.registration import register


register(
    id="instigo-goma-rl-v0",
    entry_point="CustomGymEnvSetup.environment.env:SumoEnvironment",
     kwargs={"fixed_ts": False},
)
