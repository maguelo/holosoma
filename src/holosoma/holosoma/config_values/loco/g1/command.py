"""Locomotion command presets for the G1 robot."""

from holosoma.config_types.command import CommandManagerCfg, CommandTermCfg

g1_29dof_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 10.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 1.0,
                "gait_period_randomization_width": 0.2,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [-1.0, 1.0],
                    "lin_vel_y": [-1.0, 1.0],
                    "ang_vel_yaw": [-1.0, 1.0],
                    "heading": [-3.14, 3.14],
                },
                "stand_prob": 0.2,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

g1_29dof_running_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 10.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 0.5,
                "gait_period_randomization_width": 0.1,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [-0.5, 3.5],
                    "lin_vel_y": [-0.5, 0.5],
                    "ang_vel_yaw": [-0.5, 0.5],
                    "heading": [-3.14, 3.14],
                },
                "stand_prob": 0.05,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

# Eval-only: comando fijo "correr hacia delante" para evaluación controlada
# Eval-only: avanzar recto a 1.0 m/s — para walking (gait 1.0s) y jog/exp_002 (gait 0.5s)
g1_29dof_run_forward_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 10.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 0.5,
                "gait_period_randomization_width": 0.0,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [1.0, 1.0],
                    "lin_vel_y": [0.0, 0.0],
                    "ang_vel_yaw": [0.0, 0.0],
                    "heading": [0.0, 0.0],
                },
                "stand_prob": 0.0,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

# Eval-only: sprint a 2.0 m/s — para exp_006 sprint3 (gait 0.5s)
g1_29dof_sprint_forward_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 10.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 0.5,
                "gait_period_randomization_width": 0.0,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [2.0, 2.0],
                    "lin_vel_y": [0.0, 0.0],
                    "ang_vel_yaw": [0.0, 0.0],
                    "heading": [0.0, 0.0],
                },
                "stand_prob": 0.0,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

# Training: sprint etapa 1 — rango estrecho y siempre hacia delante para que
# trotar en el sitio no pueda esconderse en la media (lección de exp_002)
g1_29dof_sprint_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 10.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 0.5,
                "gait_period_randomization_width": 0.05,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [0.5, 2.0],
                    "lin_vel_y": [-0.3, 0.3],
                    "ang_vel_yaw": [-0.3, 0.3],
                    "heading": [-3.14, 3.14],
                },
                "stand_prob": 0.0,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

# Training: sprint etapa 3 — tracking_lin > feet_phase para romper el óptimo local del trote en el sitio
g1_29dof_sprint3_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 10.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 0.5,
                "gait_period_randomization_width": 0.05,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [1.0, 2.5],
                    "lin_vel_y": [-0.2, 0.2],
                    "ang_vel_yaw": [-0.2, 0.2],
                    "heading": [-3.14, 3.14],
                },
                "stand_prob": 0.0,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

# Training: sprint etapa 2 — ampliar a 3 m/s, yaw casi nulo para eliminar el giro (lección exp_004)
g1_29dof_sprint2_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 10.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 0.5,
                "gait_period_randomization_width": 0.05,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [1.0, 3.0],
                    "lin_vel_y": [-0.2, 0.2],
                    "ang_vel_yaw": [-0.1, 0.1],
                    "heading": [-3.14, 3.14],
                },
                "stand_prob": 0.0,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

# Training: strafe rápido tipo portero — énfasis lateral, ráfagas cortas (resampling 5s)
g1_29dof_strafe_training_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 5.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 0.8,
                "gait_period_randomization_width": 0.1,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [-0.5, 0.5],
                    "lin_vel_y": [-1.5, 1.5],
                    "ang_vel_yaw": [-0.5, 0.5],
                    "heading": [-3.14, 3.14],
                },
                "stand_prob": 0.1,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

# Eval-only: desplazamiento lateral puro (portero) — comando fijo hacia la izquierda (+y)
g1_29dof_strafe_right_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 10.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 0.8,
                "gait_period_randomization_width": 0.0,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [0.0, 0.0],
                    "lin_vel_y": [-1.5, -1.5],
                    "ang_vel_yaw": [0.0, 0.0],
                    "heading": [0.0, 0.0],
                },
                "stand_prob": 0.0,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

g1_29dof_strafe_left_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 10.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 0.8,
                "gait_period_randomization_width": 0.0,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [0.0, 0.0],
                    "lin_vel_y": [1.5, 1.5],
                    "ang_vel_yaw": [0.0, 0.0],
                    "heading": [0.0, 0.0],
                },
                "stand_prob": 0.0,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

# Training: unified locomotion etapa 2 — igual que unified pero gait_period 0.5 ±0.1 → [0.4, 0.6]s
# Elimina las cadencias lentas (0.8-1.0s) que causaban inestabilidad a velocidades altas (≥1.5 m/s)
g1_29dof_unified2_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 10.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 0.5,
                "gait_period_randomization_width": 0.1,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [-1.5, 3.0],
                    "lin_vel_y": [-0.5, 0.5],
                    "ang_vel_yaw": [-1.0, 1.0],
                    "heading": [-3.14, 3.14],
                },
                "stand_prob": 0.10,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

# Training: unified locomotion — cubre parado → sprint + backwards + giros completos
# gait_period 0.7 ±0.3 → muestrea [0.4, 1.0]s: la policy aprende la cadencia óptima por velocidad
g1_29dof_unified_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 10.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 0.7,
                "gait_period_randomization_width": 0.3,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [-1.5, 3.0],
                    "lin_vel_y": [-0.5, 0.5],
                    "ang_vel_yaw": [-1.0, 1.0],
                    "heading": [-3.14, 3.14],
                },
                "stand_prob": 0.10,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

# Eval-only: marcha atrás a 1.0 m/s con cadencia media (gait 0.7s)
g1_29dof_unified_backward_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 10.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 0.7,
                "gait_period_randomization_width": 0.0,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [-1.0, -1.0],
                    "lin_vel_y": [0.0, 0.0],
                    "ang_vel_yaw": [0.0, 0.0],
                    "heading": [0.0, 0.0],
                },
                "stand_prob": 0.0,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

# Eval-only: giro en el sitio a 1.0 rad/s
g1_29dof_unified_turn_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 10.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 0.7,
                "gait_period_randomization_width": 0.0,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [0.0, 0.0],
                    "lin_vel_y": [0.0, 0.0],
                    "ang_vel_yaw": [1.0, 1.0],
                    "heading": [0.0, 0.0],
                },
                "stand_prob": 0.0,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

__all__ = [
    "g1_29dof_command",
    "g1_29dof_running_command",
    "g1_29dof_sprint_command",
    "g1_29dof_sprint2_command",
    "g1_29dof_sprint3_command",
    "g1_29dof_run_forward_command",
    "g1_29dof_sprint_forward_command",
    "g1_29dof_strafe_training_command",
    "g1_29dof_strafe_left_command",
    "g1_29dof_strafe_right_command",
    "g1_29dof_unified_command",
    "g1_29dof_unified2_command",
    "g1_29dof_unified_backward_command",
    "g1_29dof_unified_turn_command",
]
