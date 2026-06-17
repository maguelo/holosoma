"""Default command manager configurations."""

from holosoma.config_values.loco.g1.command import (
    g1_29dof_command,
    g1_29dof_run_forward_command,
    g1_29dof_sprint_forward_command,
    g1_29dof_strafe_left_command,
    g1_29dof_strafe_right_command,
    g1_29dof_unified_backward_command,
    g1_29dof_unified_turn_command,
)
from holosoma.config_values.loco.t1.command import t1_29dof_command
from holosoma.config_values.wbt.g1.command import (
    g1_29dof_wbt_command,
    g1_29dof_wbt_command_w_object,
)

none = None

DEFAULTS = {
    "none": none,
    "t1_29dof": t1_29dof_command,
    "g1_29dof": g1_29dof_command,
    "g1_29dof_run_forward": g1_29dof_run_forward_command,
    "g1_29dof_strafe_left": g1_29dof_strafe_left_command,
    "g1_29dof_strafe_right": g1_29dof_strafe_right_command,
    "g1_29dof_sprint_forward": g1_29dof_sprint_forward_command,
    "g1_29dof_unified_backward": g1_29dof_unified_backward_command,
    "g1_29dof_unified_turn": g1_29dof_unified_turn_command,
    "g1_29dof_wbt": g1_29dof_wbt_command,
    "g1_29dof_wbt_w_object": g1_29dof_wbt_command_w_object,
}
