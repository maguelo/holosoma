"""Scripted trajectory evaluation using a single checkpoint.

Runs a fixed command sequence through a locomotion policy:
  1. Walk  2 m  forward     (vx= 1.0, vy= 0.0, yaw= 0.0)
  2. Turn  90°  left        (vx= 0.0, vy= 0.0, yaw= 1.0)
  3. Strafe    left  2 m    (vx= 0.0, vy= 1.0, yaw= 0.0)
  4. Walk  5 m  forward     (vx= 1.0, vy= 0.0, yaw= 0.0)
  5. Turn  90°  left        (vx= 0.0, vy= 0.0, yaw= 1.0)
  6. Strafe    right 2 m    (vx= 0.0, vy=-1.0, yaw= 0.0)
  7. Run   5 m  return      (vx= 1.0, vy= 0.0, yaw= 0.0)  ← robot faces return dir after 2×90° turns

All segments use model_24999.pt (exp_001 walking policy, gait 1.0 s).

Usage (inside container, after source scripts/source_mujoco_setup.sh):

    python /humanoids/loop/eval_sequence.py \\
        --checkpoint logs/hv-g1-manager/20260605_141231-g1_29dof_manager-locomotion/model_24999.pt \\
        --output /tmp/eval_sequence.npz

Tip: pass --no-viewer to run headless (recording only, no MuJoCo viewer window).
"""

from __future__ import annotations

import argparse
import itertools
import math
import sys
from dataclasses import dataclass
from typing import List, Tuple

import torch

# ---------------------------------------------------------------------------
# Segment definition
# ---------------------------------------------------------------------------

@dataclass
class Segment:
    name: str
    vx: float
    vy: float
    yaw: float
    duration_s: float  # wall-clock seconds at policy frequency


def build_sequence(dt: float) -> List[Tuple[Segment, int]]:
    """Basic sequence: walk → run → turns → strafe → return."""
    turn_90_s = math.pi / 2

    segments = [
        Segment("stand_ready",       vx= 0.0, vy= 0.0, yaw= 0.0, duration_s=3.0),
        Segment("walk_forward",      vx= 1.0, vy= 0.0, yaw= 0.0, duration_s=5.0),
        Segment("run_forward",       vx= 2.0, vy= 0.0, yaw= 0.0, duration_s=5.0),
        Segment("turn_left_90",      vx= 0.0, vy= 0.0, yaw= 1.0, duration_s=turn_90_s),
        Segment("strafe_left",       vx= 0.0, vy= 1.0, yaw= 0.0, duration_s=5.0),
        Segment("walk_forward",      vx= 1.0, vy= 0.0, yaw= 0.0, duration_s=5.0),
        Segment("run_forward",       vx= 2.0, vy= 0.0, yaw= 0.0, duration_s=5.0),
        Segment("turn_left_90",      vx= 0.0, vy= 0.0, yaw= 1.0, duration_s=turn_90_s),
        Segment("strafe_right",      vx= 0.0, vy=-1.0, yaw= 0.0, duration_s=5.0),
        Segment("walk_forward",      vx= 1.0, vy= 0.0, yaw= 0.0, duration_s=5.0),
        Segment("run_return",        vx= 2.0, vy= 0.0, yaw= 0.0, duration_s=5.0),
        Segment("backward",          vx=-1.0, vy= 0.0, yaw= 0.0, duration_s=5.0),
    ]
    return [(seg, max(1, round(seg.duration_s / dt))) for seg in segments]


def build_football_sequence(dt: float) -> List[Tuple[Segment, int]]:
    """Football circuit — pushes diagonal movement, cuts, sprints and quick pivots.

    Sequence narrative (unified model, vx up to 2.5 m/s):
      1.  Kickoff sprint         — flat out forward
      2.  Cut right diagonal     — sprint + strafe right simultaneously
      3.  Straighten & accelerate
      4.  Cut left diagonal      — sprint + strafe left simultaneously
      5.  Pure sprint            — reaccelerate after cut
      6.  Strafe right (lateral) — goalkeeper-style repositioning
      7.  Sprint + drift right   — running with slight lateral offset
      8.  Quick pivot left       — sharp yaw turn at partial speed
      9.  Sprint new direction
      10. Diagonal back-right    — retreat while drifting right (defender move)
      11. Strafe left reposition
      12. Final sprint           — maximum effort
    """
    pivot_s = math.pi / 3  # 60° turn at 1.0 rad/s ≈ 1.05 s  (faster than 90°)

    segments = [
        # ── Phase 0: stand still ─────────────────────────────────────────
        Segment("stand_ready",           vx= 0.0, vy= 0.0, yaw= 0.0, duration_s=3.0),

        # ── Phase 1: kickoff ──────────────────────────────────────────────
        Segment("kickoff_walk",          vx= 1.0, vy= 0.0, yaw= 0.0, duration_s=1.5),
        Segment("kickoff_sprint",        vx= 2.0, vy= 0.0, yaw= 0.0, duration_s=2.0),

        # ── Phase 2: diagonal cut right (sprint + strafe) ─────────────────
        Segment("cut_diagonal_right",    vx= 2.0, vy=-1.0, yaw= 0.0, duration_s=3.0),
        Segment("reaccelerate",          vx= 2.0, vy= 0.0, yaw= 0.0, duration_s=3.0),

        # ── Phase 3: diagonal cut left ────────────────────────────────────
        Segment("cut_diagonal_left",     vx= 2.0, vy= 1.0, yaw= 0.0, duration_s=3.0),
        Segment("sprint_after_cut",      vx= 2.0, vy= 0.0, yaw= 0.0, duration_s=3.0),

        # ── Phase 4: lateral repositioning (pure strafe) ──────────────────
        Segment("strafe_right",          vx= 0.0, vy=-1.0, yaw= 0.0, duration_s=3.0),
        Segment("strafe_left",           vx= 0.0, vy= 1.0, yaw= 0.0, duration_s=3.0),

        # ── Phase 5: sprint with lateral drift ────────────────────────────
        Segment("sprint_drift_right",    vx= 2.0, vy=-0.5, yaw= 0.0, duration_s=3.0),

        # ── Phase 6: quick pivot + new direction ──────────────────────────
        Segment("pivot_left_60",         vx= 0.5, vy= 0.0, yaw= 1.0, duration_s=pivot_s),
        Segment("sprint_new_direction",  vx= 2.0, vy= 0.0, yaw= 0.0, duration_s=3.0),

        # ── Phase 7: defender retreat (backward + lateral) ────────────────
        Segment("retreat_diagonal",      vx=-1.0, vy=-0.5, yaw= 0.0, duration_s=3.0),
        Segment("strafe_reposition",     vx= 0.0, vy= 1.0, yaw= 0.0, duration_s=3.0),

        # ── Phase 8: final maximum sprint ─────────────────────────────────
        Segment("final_sprint",          vx= 2.0, vy= 0.0, yaw= 0.0, duration_s=3.0),
    ]
    return [(seg, max(1, round(seg.duration_s / dt))) for seg in segments]


CIRCUITS = {
    "basic":    build_sequence,
    "football": build_football_sequence,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--checkpoint", required=True, help="Path to .pt checkpoint")
    p.add_argument("--output", default="/tmp/eval_sequence.npz", help="Output .npz path for recording")
    p.add_argument("--no-viewer", action="store_true", help="Disable MuJoCo viewer (headless)")
    p.add_argument("--circuit", choices=list(CIRCUITS), default="basic",
                   help="Which movement circuit to run (default: basic)")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # --- holosoma imports (must happen after MuJoCo env is ready) -----------
    import tyro
    from holosoma.config_types.eval_callback import (
        EvalCallbacksConfig,
        RecordingCallbackConfig,
        RecordingConfig,
    )
    from holosoma.config_types.experiment import ExperimentConfig
    from holosoma.utils.eval_utils import (
        CheckpointConfig,
        init_eval_logging,
        load_checkpoint,
        load_saved_experiment_config,
    )
    from holosoma.utils.experiment_paths import get_experiment_dir, get_timestamp
    from holosoma.utils.helpers import get_class
    from holosoma.utils.sim_utils import close_simulation_app, setup_simulation_environment
    from holosoma.utils.tyro_utils import TYRO_CONIFG

    init_eval_logging()

    # --- load saved config from checkpoint dir ------------------------------
    checkpoint_cfg = CheckpointConfig(checkpoint=args.checkpoint)
    saved_cfg, saved_wandb_path = load_saved_experiment_config(checkpoint_cfg)
    eval_cfg = saved_cfg.get_eval_config()

    # Override simulator settings — recording flags go via EvalCallbacksConfig, not here
    extra_args = [
        "--simulator.config.mujoco-backend", "CLASSIC",
        "--randomization.ignore-unsupported", "True",
    ]
    if args.no_viewer:
        extra_args += ["--simulator.config.headless", "True"]

    tyro_config: ExperimentConfig = tyro.cli(
        ExperimentConfig,
        default=eval_cfg,
        args=extra_args,
        description="eval_sequence overrides",
        config=TYRO_CONIFG,
    )

    # Build recording callback and inject into algo config BEFORE constructing algo
    # (mirrors run_eval_with_tyro in eval_agent.py — must happen before algo.__init__)
    eval_cbs_cfg = EvalCallbacksConfig(
        recording=RecordingCallbackConfig(
            config=RecordingConfig(enabled=True, output_path=args.output)
        )
    )
    cb_configs = eval_cbs_cfg.collect_active_callbacks()
    if cb_configs:
        object.__setattr__(tyro_config.algo.config, "eval_callbacks", cb_configs)

    # --- set up env ---------------------------------------------------------
    env, device, simulation_app = setup_simulation_environment(tyro_config)

    eval_log_dir = get_experiment_dir(
        tyro_config.logger, tyro_config.training, get_timestamp(), task_name="eval_sequence"
    )
    eval_log_dir.mkdir(parents=True, exist_ok=True)

    checkpoint = load_checkpoint(args.checkpoint, str(eval_log_dir))
    checkpoint_path = str(checkpoint)

    algo_class = get_class(tyro_config.algo._target_)
    algo = algo_class(
        device=device,
        env=env,
        config=tyro_config.algo.config,
        log_dir=str(eval_log_dir),
        multi_gpu_cfg=None,
    )
    algo.setup()
    algo.attach_checkpoint_metadata(saved_cfg, saved_wandb_path)
    algo.load(checkpoint_path)

    # --- eval setup (mirrors PPO.evaluate_policy exactly) ------------------
    algo._create_eval_callbacks()
    algo._pre_evaluate_policy()                       # eval mode + env reset + on_pre callbacks
    algo.eval_policy = algo.get_inference_policy()    # required by _pre_eval_env_step

    obs_dict = env.reset_all()                        # second reset → fresh obs for actor_state
    actor_state = algo._create_actor_state()
    init_actions = torch.zeros(env.num_envs, algo.num_act, device=device)
    actor_state.update({"obs": obs_dict, "actions": init_actions})

    critic_obs = torch.cat([actor_state["obs"][k] for k in algo.critic_obs_keys], dim=1)
    actor_state["obs"]["critic_obs"] = critic_obs

    # warm-up pre-step (initialises recorder etc.)
    actor_state = algo._pre_eval_env_step(actor_state)

    # --- build sequence using actual env dt --------------------------------
    sequence = CIRCUITS[args.circuit](env.dt)

    total_steps = sum(n for _, n in sequence)
    print(f"\n[eval_sequence] circuit={args.circuit}  dt={env.dt:.4f}s  total steps={total_steps} ({total_steps*env.dt:.1f}s)")
    for seg, n in sequence:
        print(f"  {seg.name:<22} vx={seg.vx:+.1f} vy={seg.vy:+.1f} yaw={seg.yaw:+.1f}  "
              f"{n} steps ({n*env.dt:.2f}s)")
    print()

    # --- run sequence -------------------------------------------------------
    commands: torch.Tensor = env.command_manager.commands  # (num_envs, ≥3)

    global_step = 0
    for seg, num_steps in sequence:
        cmd = torch.tensor([seg.vx, seg.vy, seg.yaw], device=device, dtype=commands.dtype)
        # broadcast across all envs and cmd dims (pad extra dims with 0)
        commands.zero_()
        commands[:, :3] = cmd.unsqueeze(0).expand(env.num_envs, -1)

        print(f"[eval_sequence] → {seg.name} ({num_steps} steps)")
        for _ in range(num_steps):
            actor_state["step"] = global_step

            # re-inject command every step so resampling can't override it
            commands[:, :3] = cmd.unsqueeze(0).expand(env.num_envs, -1)

            actor_state = algo._pre_eval_env_step(actor_state)
            actor_state = algo.env_step(actor_state)
            actor_state = algo._post_eval_env_step(actor_state)
            global_step += 1

    # --- teardown -----------------------------------------------------------
    algo._post_evaluate_policy()

    if simulation_app:
        close_simulation_app(simulation_app)

    print(f"\n[eval_sequence] Done. Recording saved to {args.output}")


if __name__ == "__main__":
    main()
