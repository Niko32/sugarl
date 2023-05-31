# SUGARL
Code for Active Reinforcement Learning with Limited Visual Observability, by [Jinghuan Shang](https://www.cs.stonybrook.edu/~jishang) and [Michael S. Ryoo](http://michaelryoo.com/).
We propose Sensorimotor Understanding Guided Active Reinforcement Learning (SUGARL) to solve Active-RL tasks.
We also introduce [Active-Gym](https://github.com/elicassion/active-gym), a convenient library that modifies existing RL environments for Active-RL , with Gymnasium-like interface.

[[Project Page]](https://elicassion.github.io/sugarl/sugarl.html) [[Active-Gym]](https://github.com/elicassion/active-gym)

<img width="100%" src="_doc/media/sugarl_formulation.png">

## Dependency
```
conda env create -f active_rl_env.yaml
```
We highlight [Active-Gym](https://github.com/elicassion/active-gym) developed by us to support Active-RL setting for many environments.


## Usage
- General format:
```
cd sugarl       # make sure you are under the root dir of this repo
bash ./scripts/<any_setting.sh> agent/<any_agent_valid_for_that_setting.py>
```

- Reproduce our experiments:
```
cd sugarl       # make sure you are under the root dir of this repo
bash ./scripts/atari_series.sh agent/<any_agent_valid_for_that_setting.py>
bash ./scripts/atari_series_5m.sh agent/<any_agent_valid_for_that_setting.py>
bash ./scripts/atari_wp_series.sh agent/<any_agent_valid_for_that_setting.py>
bash ./scripts/dmc_series.sh agent/<any_agent_valid_for_that_setting.py>
```

- Sanity checks: they run through the whole process with only a tiny amount of training to check bugs
```
cd sugarl       # make sure you are under the root dir of this repo
bash ./scripts/atari_test.sh agent/<any_agent_valid_for_your_test.py>
bash ./scripts/dmc_test.sh agent/<any_agent_valid_for_your_test.py>
```

### Notes
**Naming**:

All agents are under `agent/`, with the name format `<base_algorithm>_<env>_<variant>.py`. Each file is an individual entry for the whole process.

All experiment scripts are under `scripts/`, with the format `<env>_<setting>.sh`
Please ensure that the env and setting match the agent when launching jobs.

All experiment scripts automatically scale all tasks to your GPUs. Please modify the gpu behavior (`CUDA_VISIBLE_DEVICES=<x>`) in the script if
- you are sharing GPU with others
- either VRAM or RAM is not sufficient for scaling all jobs

**Resource requirement reference (SUGARL)**:

- Atari:
for each game with `100k` replay buffer: `~18G` RAM, `<2G` VRAM

- DMC:
for each task with `100k` replay buffer: `~18G` RAM, `<3G` VRAM

**Coding style**:

We follow the coding style of [clean-rl](https://github.com/vwxyzjn/cleanrl) so that modifications on one agent would not affect others. This does introduce lots of redundency, but is so much easier for arranging experiments and evolving the algorithm.

## Citation
Please consider cite us if you find this repo helpful.

## Acknowledgement
We thank the implementation of [clean-rl](https://github.com/vwxyzjn/cleanrl).