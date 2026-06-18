#!/usr/bin/env python3
"""Extrae métricas clave de un run de holosoma (TFEvents) a JSON.

Se ejecuta dentro del container (necesita tensorboard):
    docker run --rm -v <logs>:/logs -v <este_dir>:/loop holosoma-mujoco-lite:latest \
        python3 /loop/extract_metrics.py /logs/<run_dir> -o /loop/out.json

O en cualquier entorno con `pip install tensorboard`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KEY_TAGS = [
    "Train/mean_reward",
    "Train/mean_episode_length",
    "Episode/rew_tracking_lin_vel",
    "Episode/rew_tracking_ang_vel",
    "Episode/rew_alive",
    "Episode/rew_feet_phase",
    "Episode/rew_penalty_orientation",
    "Episode/rew_penalty_close_feet_xy",
    "Env/penalty_scale",
    "Loss/KL",
    "Policy/mean_noise_std",
]


def extract(run_dir: Path, num_samples: int = 10) -> dict:
    from tensorboard.backend.event_processing import event_accumulator

    ea = event_accumulator.EventAccumulator(str(run_dir))
    ea.Reload()
    available = set(ea.Tags()["scalars"])

    result: dict = {"run_dir": str(run_dir), "tags": {}}
    for tag in KEY_TAGS:
        if tag not in available:
            result["tags"][tag] = None
            continue
        events = ea.Scalars(tag)
        step = max(1, len(events) // num_samples)
        sampled = events[::step]
        if events and events[-1].step != sampled[-1].step:
            sampled.append(events[-1])
        result["tags"][tag] = {
            "first": {"iter": events[0].step, "value": events[0].value},
            "last": {"iter": events[-1].step, "value": events[-1].value},
            "history": [{"iter": e.step, "value": round(e.value, 4)} for e in sampled],
        }

    # Resumen rápido para comparar runs de un vistazo
    def last(tag: str):
        t = result["tags"].get(tag)
        return round(t["last"]["value"], 4) if t else None

    result["summary"] = {
        "final_iteration": result["tags"]["Train/mean_reward"]["last"]["iter"]
        if result["tags"]["Train/mean_reward"]
        else None,
        "mean_reward": last("Train/mean_reward"),
        "episode_length": last("Train/mean_episode_length"),
        "tracking_lin_vel": last("Episode/rew_tracking_lin_vel"),
        "tracking_ang_vel": last("Episode/rew_tracking_ang_vel"),
        "alive": last("Episode/rew_alive"),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="Directorio del run (contiene events.out.tfevents.*)")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Fichero JSON de salida (default: stdout)")
    parser.add_argument("-n", "--num-samples", type=int, default=10, help="Puntos del historial por métrica")
    args = parser.parse_args()

    if not args.run_dir.is_dir():
        print(f"ERROR: {args.run_dir} no es un directorio", file=sys.stderr)
        return 1
    if not list(args.run_dir.glob("events.out.tfevents.*")):
        print(f"ERROR: no hay TFEvents en {args.run_dir}", file=sys.stderr)
        return 1

    result = extract(args.run_dir, args.num_samples)
    output = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(output)
        print(f"Métricas guardadas en {args.output}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
