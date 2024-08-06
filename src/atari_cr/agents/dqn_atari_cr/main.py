import argparse
import os
from distutils.util import strtobool

os.environ["OMP_NUM_THREADS"] = "1"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import gymnasium as gym
import torch

from active_gym.atari_env import AtariEnv, AtariEnvArgs, AtariFixedFovealEnv

from atari_cr.common.utils import seed_everything, get_sugarl_reward_scale_atari
from atari_cr.common.pauseable_env import PauseableFixedFovealEnv
from atari_cr.common.models import SensoryActionMode
from atari_cr.agents.dqn_atari_cr.crdqn import CRDQN

# TODO: Remove normal pause cost in favor of a bigger penalty for 30 pauses in a row
# TODO: Do 20M steps (propably not veeery helpful)
# TODO: Test realtive actions better
# TODO: Go back to absolute actions because they are not really worse from a cr perspective
# TODO: Test other games
# TODO: Add saccade costs for foveal distance traveled

# TODO: Weitermachen mit Road Runner, Ms. Pac-Man, und Breakout; Boxing ist nicht in Atari-HEAD 


def parse_args():
    # fmt: off
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-name", type=str, default=os.path.basename(__file__).rstrip(".py"),
        help="the name of this experiment")
    parser.add_argument("--seed", type=int, default=1,
        help="seed of the experiment")
    parser.add_argument("--cuda", type=lambda x: bool(strtobool(x)), default=True, nargs="?", const=True,
        help="if toggled, cuda will be enabled by default")
    parser.add_argument("--capture-video", type=lambda x: bool(strtobool(x)), default=False, nargs="?", const=True,
        help="whether to capture videos of the agent performances (check out `videos` folder)")

    # env setting
    parser.add_argument("--env", type=str, default="breakout",
        help="the id of the environment")
    parser.add_argument("--env-num", type=int, default=1, 
        help="# envs in parallel")
    parser.add_argument("--frame-stack", type=int, default=4,
        help="frame stack #")
    parser.add_argument("--action-repeat", type=int, default=4,
        help="action repeat #")
    parser.add_argument("--clip-reward", type=lambda x: bool(strtobool(x)), default=False, nargs="?", const=True)

    # fov setting
    parser.add_argument("--fov-size", type=int, default=50)
    parser.add_argument("--fov-init-loc", type=int, default=0)
    parser.add_argument("--sensory-action-mode", type=str, default="absolute",
        help="How the sensory action is interpreted by the env. Either 'absolute' or 'relative'")
    parser.add_argument("--sensory-action-space", type=int, default=10,
        help="Maximum size of pixels to move the fovea in one relative sensory step. Ignored for absolute sensory action mode") 
    parser.add_argument("--resize-to-full", default=False, action="store_true")
    # for discrete observ action
    parser.add_argument("--sensory-action-x-size", type=int, default=4)
    parser.add_argument("--sensory-action-y-size", type=int, default=4)
    # pvm setting
    parser.add_argument("--pvm-stack", type=int, default=3)

    # Algorithm specific arguments
    parser.add_argument("--total-timesteps", type=int, default=3000000,
        help="total timesteps of the experiments")
    parser.add_argument("--learning-rate", type=float, default=1e-4,
        help="the learning rate of the self.optimizer")
    parser.add_argument("--buffer-size", type=int, default=500000,
        help="the replay memory buffer size")
    parser.add_argument("--gamma", type=float, default=0.99,
        help="the discount factor gamma")
    parser.add_argument("--target-network-frequency", type=int, default=1000,
        help="the timesteps it takes to update the target network")
    parser.add_argument("--batch-size", type=int, default=32,
        help="the batch size of sample from the reply memory")
    parser.add_argument("--start-e", type=float, default=1,
        help="the starting epsilon for exploration")
    parser.add_argument("--end-e", type=float, default=0.01,
        help="the ending epsilon for exploration")
    parser.add_argument("--exploration-fraction", type=float, default=0.10,
        help="the fraction of `total-timesteps` it takes from start-e to go end-e")
    parser.add_argument("--learning-start", type=int, default=80000,
        help="timestep to start learning")
    parser.add_argument("--train-frequency", type=int, default=4,
        help="the frequency of training")

    # eval args
    parser.add_argument("--eval-frequency", type=int, default=-1,
        help="eval frequency. default -1 is eval at the end.")
    parser.add_argument("--eval-num", type=int, default=10,
        help="eval frequency. default -1 is eval at the end.")
    
    # Pause args
    parser.add_argument("--pause-cost", type=float, default=0.01,
        help="Cost for looking without taking an env action. Prevents the agent from abusing too many pauses")
    parser.add_argument("--successive-pause-limit", type=int, default=20,
        help="Limit to the amount of successive pauses the agent can make before a random action is selected instead. \
            This prevents the agent from halting")
    parser.add_argument("--ignore-sugarl", action="store_true",
        help="Whether to ignore the sugarl term in the loss calculation")
    parser.add_argument("--no-action-pause-cost", type=float, default=0.1,
        help="Penalty for performing a useless pause without a sensory action. This is meant to speed up training")
    parser.add_argument("--grokfast", action="store_true")
    parser.add_argument("--no-pause-env", action="store_true",
        help="Whether to use the normal sugarl setting without a pausable env.")
    
    args = parser.parse_args()
    return args

def make_env(seed, **kwargs):
    def thunk():
        env_args = AtariEnvArgs(
            game=args.env, 
            seed=args.seed + seed, 
            obs_size=(84, 84), 
            frame_stack=args.frame_stack, 
            action_repeat=args.action_repeat,
            fov_size=(args.fov_size, args.fov_size), 
            fov_init_loc=(args.fov_init_loc, args.fov_init_loc),
            sensory_action_mode=sensory_action_mode,
            sensory_action_space=(-args.sensory_action_space, args.sensory_action_space),
            resize_to_full=args.resize_to_full,
            clip_reward=args.clip_reward,
            mask_out=True,
            **kwargs
        )
        if args.no_pause_env:
            env_args.sensory_action_mode = str(sensory_action_mode)
            env = AtariFixedFovealEnv(env_args)
        else:
            env = AtariEnv(env_args)    
            env = PauseableFixedFovealEnv(env, env_args, 
                args.pause_cost, args.successive_pause_limit, args.no_action_pause_cost)
        env.action_space.seed(seed)
        env.observation_space.seed(seed)
        return env

    return thunk

def make_train_env():
    envs = [make_env(i) for i in range(args.env_num)]
    return gym.vector.SyncVectorEnv(envs)

def make_eval_env(seed):
    envs = [make_env(seed, training=False, record=args.capture_video)]
    return gym.vector.SyncVectorEnv(envs)

if __name__ == "__main__":
    args = parse_args()
    sensory_action_mode = SensoryActionMode.from_string(args.sensory_action_mode)

    seed_everything(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() and args.cuda else "cpu")
    assert device.type == "cuda"

    sugarl_r_scale = get_sugarl_reward_scale_atari(args.env)

    env = make_train_env()
    agent = CRDQN(
        env, 
        make_eval_env, 
        sugarl_r_scale,
        seed=args.seed,
        fov_size=args.fov_size,
        replay_buffer_size=args.buffer_size,
        learning_start=args.learning_start,
        pvm_stack=args.pvm_stack,
        grokfast=args.grokfast
    )

    agent.learn(args.total_timesteps, args.env, args.exp_name)