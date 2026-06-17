from dataclasses import replace

from holosoma.config_types.experiment import ExperimentConfig, NightlyConfig, TrainingConfig
from holosoma.config_values import (
    action,
    algo,
    command,
    curriculum,
    observation,
    randomization,
    reward,
    robot,
    simulator,
    termination,
    terrain,
)
from holosoma.config_values.loco.g1.command import (
    g1_29dof_running_command,
    g1_29dof_sprint_command,
    g1_29dof_sprint2_command,
    g1_29dof_sprint3_command,
    g1_29dof_strafe_training_command,
    g1_29dof_unified_command,
    g1_29dof_unified2_command,
)
from holosoma.config_values.loco.g1.reward import (
    g1_29dof_running_loco,
    g1_29dof_sprint2_loco,
    g1_29dof_sprint3_loco,
    g1_29dof_strafe_loco,
    g1_29dof_unified_loco,
)

g1_29dof = ExperimentConfig(
    env_class="holosoma.envs.locomotion.locomotion_manager.LeggedRobotLocomotionManager",
    training=TrainingConfig(project="hv-g1-manager", name="g1_29dof_manager"),
    algo=replace(algo.ppo, config=replace(algo.ppo.config, num_learning_iterations=25000, use_symmetry=True)),
    simulator=simulator.isaacgym,
    robot=robot.g1_29dof,
    terrain=terrain.terrain_locomotion_mix,
    observation=observation.g1_29dof_loco_single_wolinvel,
    action=action.g1_29dof_joint_pos,
    termination=termination.g1_29dof_termination,
    randomization=randomization.g1_29dof_randomization,
    command=command.g1_29dof_command,
    curriculum=curriculum.g1_29dof_curriculum,
    reward=reward.g1_29dof_loco,
    nightly=NightlyConfig(
        iterations=5000,
        metrics={"Episode/rew_tracking_ang_vel": [0.7, "inf"], "Episode/rew_tracking_lin_vel": [0.55, "inf"]},
    ),
)

g1_29dof_fast_sac = ExperimentConfig(
    env_class="holosoma.envs.locomotion.locomotion_manager.LeggedRobotLocomotionManager",
    training=TrainingConfig(project="hv-g1-manager", name="g1_29dof_fast_sac_manager"),
    algo=replace(algo.fast_sac, config=replace(algo.fast_sac.config, num_learning_iterations=50000, use_symmetry=True)),
    simulator=simulator.isaacgym,
    robot=robot.g1_29dof,
    terrain=terrain.terrain_locomotion_mix,
    observation=observation.g1_29dof_loco_single_wolinvel,
    action=action.g1_29dof_joint_pos,
    termination=termination.g1_29dof_termination,
    randomization=randomization.g1_29dof_randomization,
    command=command.g1_29dof_command,
    curriculum=curriculum.g1_29dof_curriculum_fast_sac,
    reward=reward.g1_29dof_loco_fast_sac,
    nightly=NightlyConfig(
        iterations=50000,
        metrics={"Episode/rew_tracking_ang_vel": [0.8, "inf"], "Episode/rew_tracking_lin_vel": [0.95, "inf"]},
    ),
)

g1_29dof_running = ExperimentConfig(
    env_class="holosoma.envs.locomotion.locomotion_manager.LeggedRobotLocomotionManager",
    training=TrainingConfig(project="hv-g1-manager", name="g1_29dof_running_manager"),
    algo=replace(algo.ppo, config=replace(algo.ppo.config, num_learning_iterations=25000, use_symmetry=True)),
    simulator=simulator.mjwarp,
    robot=robot.g1_29dof,
    terrain=terrain.terrain_locomotion_mix,
    observation=observation.g1_29dof_loco_single_wolinvel,
    action=action.g1_29dof_joint_pos,
    termination=termination.g1_29dof_termination,
    randomization=randomization.g1_29dof_randomization,
    command=g1_29dof_running_command,
    curriculum=curriculum.g1_29dof_curriculum,
    reward=g1_29dof_running_loco,
    nightly=NightlyConfig(
        iterations=5000,
        metrics={"Episode/rew_tracking_ang_vel": [0.5, "inf"], "Episode/rew_tracking_lin_vel": [0.7, "inf"]},
    ),
)

g1_29dof_strafe = ExperimentConfig(
    env_class="holosoma.envs.locomotion.locomotion_manager.LeggedRobotLocomotionManager",
    training=TrainingConfig(project="hv-g1-manager", name="g1_29dof_strafe_manager"),
    algo=replace(algo.ppo, config=replace(algo.ppo.config, num_learning_iterations=10000, use_symmetry=True)),
    simulator=simulator.mjwarp,
    robot=robot.g1_29dof,
    terrain=terrain.terrain_locomotion_mix,
    observation=observation.g1_29dof_loco_single_wolinvel,
    action=action.g1_29dof_joint_pos,
    termination=termination.g1_29dof_termination,
    randomization=randomization.g1_29dof_randomization,
    command=g1_29dof_strafe_training_command,
    curriculum=curriculum.g1_29dof_curriculum,
    reward=g1_29dof_strafe_loco,
    nightly=NightlyConfig(
        iterations=5000,
        metrics={"Episode/rew_tracking_ang_vel": [0.7, "inf"], "Episode/rew_tracking_lin_vel": [1.65, "inf"]},
    ),
)

g1_29dof_sprint = ExperimentConfig(
    env_class="holosoma.envs.locomotion.locomotion_manager.LeggedRobotLocomotionManager",
    training=TrainingConfig(project="hv-g1-manager", name="g1_29dof_sprint_manager"),
    algo=replace(algo.ppo, config=replace(algo.ppo.config, num_learning_iterations=10000, use_symmetry=True)),
    simulator=simulator.mjwarp,
    robot=robot.g1_29dof,
    terrain=terrain.terrain_locomotion_mix,
    observation=observation.g1_29dof_loco_single_wolinvel,
    action=action.g1_29dof_joint_pos,
    termination=termination.g1_29dof_termination,
    randomization=randomization.g1_29dof_randomization,
    command=g1_29dof_sprint_command,
    curriculum=curriculum.g1_29dof_curriculum,
    reward=g1_29dof_running_loco,
    nightly=NightlyConfig(
        iterations=5000,
        metrics={"Episode/rew_tracking_ang_vel": [0.5, "inf"], "Episode/rew_tracking_lin_vel": [1.8, "inf"]},
    ),
)

g1_29dof_sprint2 = ExperimentConfig(
    env_class="holosoma.envs.locomotion.locomotion_manager.LeggedRobotLocomotionManager",
    training=TrainingConfig(project="hv-g1-manager", name="g1_29dof_sprint2_manager"),
    algo=replace(algo.ppo, config=replace(algo.ppo.config, num_learning_iterations=10000, use_symmetry=True)),
    simulator=simulator.mjwarp,
    robot=robot.g1_29dof,
    terrain=terrain.terrain_locomotion_mix,
    observation=observation.g1_29dof_loco_single_wolinvel,
    action=action.g1_29dof_joint_pos,
    termination=termination.g1_29dof_termination,
    randomization=randomization.g1_29dof_randomization,
    command=g1_29dof_sprint2_command,
    curriculum=curriculum.g1_29dof_curriculum,
    reward=g1_29dof_sprint2_loco,
    nightly=NightlyConfig(
        iterations=5000,
        metrics={"Episode/rew_tracking_ang_vel": [1.2, "inf"], "Episode/rew_tracking_lin_vel": [2.0, "inf"]},
    ),
)

g1_29dof_sprint3 = ExperimentConfig(
    env_class="holosoma.envs.locomotion.locomotion_manager.LeggedRobotLocomotionManager",
    training=TrainingConfig(project="hv-g1-manager", name="g1_29dof_sprint3_manager"),
    algo=replace(algo.ppo, config=replace(algo.ppo.config, num_learning_iterations=10000, use_symmetry=True)),
    simulator=simulator.mjwarp,
    robot=robot.g1_29dof,
    terrain=terrain.terrain_locomotion_mix,
    observation=observation.g1_29dof_loco_single_wolinvel,
    action=action.g1_29dof_joint_pos,
    termination=termination.g1_29dof_termination,
    randomization=randomization.g1_29dof_randomization,
    command=g1_29dof_sprint3_command,
    curriculum=curriculum.g1_29dof_curriculum,
    reward=g1_29dof_sprint3_loco,
    nightly=NightlyConfig(
        iterations=5000,
        metrics={"Episode/rew_tracking_ang_vel": [1.2, "inf"], "Episode/rew_tracking_lin_vel": [3.5, "inf"]},
    ),
)

g1_29dof_unified = ExperimentConfig(
    env_class="holosoma.envs.locomotion.locomotion_manager.LeggedRobotLocomotionManager",
    training=TrainingConfig(project="hv-g1-manager", name="g1_29dof_unified_manager"),
    algo=replace(algo.ppo, config=replace(algo.ppo.config, num_learning_iterations=15000, use_symmetry=True)),
    simulator=simulator.mjwarp,
    robot=robot.g1_29dof,
    terrain=terrain.terrain_locomotion_mix,
    observation=observation.g1_29dof_loco_single_wolinvel,
    action=action.g1_29dof_joint_pos,
    termination=termination.g1_29dof_termination,
    randomization=randomization.g1_29dof_randomization,
    command=g1_29dof_unified_command,
    curriculum=curriculum.g1_29dof_curriculum,
    reward=g1_29dof_unified_loco,
    nightly=NightlyConfig(
        iterations=5000,
        metrics={"Episode/rew_tracking_ang_vel": [1.2, "inf"], "Episode/rew_tracking_lin_vel": [3.5, "inf"]},
    ),
)

g1_29dof_unified2 = ExperimentConfig(
    env_class="holosoma.envs.locomotion.locomotion_manager.LeggedRobotLocomotionManager",
    training=TrainingConfig(project="hv-g1-manager", name="g1_29dof_unified2_manager"),
    algo=replace(algo.ppo, config=replace(algo.ppo.config, num_learning_iterations=10000, use_symmetry=True)),
    simulator=simulator.mjwarp,
    robot=robot.g1_29dof,
    terrain=terrain.terrain_locomotion_mix,
    observation=observation.g1_29dof_loco_single_wolinvel,
    action=action.g1_29dof_joint_pos,
    termination=termination.g1_29dof_termination,
    randomization=randomization.g1_29dof_randomization,
    command=g1_29dof_unified2_command,
    curriculum=curriculum.g1_29dof_curriculum,
    reward=g1_29dof_unified_loco,
    nightly=NightlyConfig(
        iterations=5000,
        metrics={"Episode/rew_tracking_ang_vel": [1.2, "inf"], "Episode/rew_tracking_lin_vel": [3.5, "inf"]},
    ),
)

__all__ = ["g1_29dof", "g1_29dof_fast_sac", "g1_29dof_running", "g1_29dof_strafe", "g1_29dof_sprint", "g1_29dof_sprint2", "g1_29dof_sprint3", "g1_29dof_unified", "g1_29dof_unified2"]
