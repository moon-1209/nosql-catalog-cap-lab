"""Actor-Critic PPO network (`PPOHospitalAgent`) for 31-D hospital observation space.

Observation vector (31-D, normalized in [-1, 1]):
- [0..16]  : 17-ray horizontal 2D LiDAR fan (200 deg FOV, 6.0 m max range)
- [17..20] : 4D YOLO target bounding box [has_det, cx - 0.5, h, conf]
- [21..24] : 4D one-hot task phase [SEARCH, APPROACH, GUIDE_ESCORT, CALL_STAFF]
- [25..27] : 3D relative goal polar vector [d_goal / 25, sin(theta_goal), cos(theta_goal)]
- [28..30] : 3D patient tether & robot velocity [d_tether / 5, v / V_MAX, omega / OMEGA_MAX]

Action vector (2-D continuous in [-1, 1]^2):
- a_v     -> v     = clamp((a_v + 1) * 0.5 * V_MAX, 0.0, V_MAX)
- a_omega -> omega = clamp(a_omega * OMEGA_MAX, -OMEGA_MAX, OMEGA_MAX)
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Normal

OBS_DIM = 31
ACT_DIM = 2
V_MAX = 0.8
OMEGA_MAX = 1.2


def _ortho_init(layer: nn.Linear, gain: float = np.sqrt(2.0)) -> nn.Linear:
    nn.init.orthogonal_(layer.weight, gain=gain)
    if layer.bias is not None:
        nn.init.constant_(layer.bias, 0.0)
    return layer


class PPOHospitalAgent(nn.Module):
    """2-layer MLP Actor-Critic (31 -> 128 -> 128) for continuous hospital navigation & escort."""

    def __init__(self, obs_dim: int = OBS_DIM, act_dim: int = ACT_DIM, hidden_dim: int = 128) -> None:
        super().__init__()
        self.obs_dim = obs_dim
        self.act_dim = act_dim

        self.actor_backbone = nn.Sequential(
            _ortho_init(nn.Linear(obs_dim, hidden_dim)),
            nn.Tanh(),
            _ortho_init(nn.Linear(hidden_dim, hidden_dim)),
            nn.Tanh(),
        )
        self.actor_mean = _ortho_init(nn.Linear(hidden_dim, act_dim), gain=0.01)
        self.actor_logstd = nn.Parameter(torch.full((1, act_dim), -0.5))

        self.critic = nn.Sequential(
            _ortho_init(nn.Linear(obs_dim, hidden_dim)),
            nn.Tanh(),
            _ortho_init(nn.Linear(hidden_dim, hidden_dim)),
            nn.Tanh(),
            _ortho_init(nn.Linear(hidden_dim, 1), gain=1.0),
        )

    def get_value(self, obs: torch.Tensor) -> torch.Tensor:
        return self.critic(obs).squeeze(-1)

    def get_action_and_value(
        self,
        obs: torch.Tensor,
        action: torch.Tensor | None = None,
        deterministic: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        hidden = self.actor_backbone(obs)
        mean = torch.tanh(self.actor_mean(hidden))
        std = torch.exp(torch.clamp(self.actor_logstd, -2.5, 0.5)).expand_as(mean)
        dist = Normal(mean, std)
        if action is None:
            raw_action = mean if deterministic else dist.sample()
            action = torch.clamp(raw_action, -1.0, 1.0)
        logprob = dist.log_prob(action).sum(-1)
        entropy = dist.entropy().sum(-1)
        value = self.critic(obs).squeeze(-1)
        return action, logprob, entropy, value

    @staticmethod
    def decode_action(a_v: float, a_omega: float) -> tuple[float, float]:
        """Convert normalized action in [-1, 1]^2 to physical (v [m/s], omega [rad/s])."""
        v = float(np.clip((a_v + 1.0) * 0.5 * V_MAX, 0.0, V_MAX))
        omega = float(np.clip(a_omega * OMEGA_MAX, -OMEGA_MAX, OMEGA_MAX))
        return v, omega
