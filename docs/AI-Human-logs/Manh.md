### D-032 — Main Entrance + Robot Dock, Grid Path Planner, Polite NPCs, and the Strongest Full-Mode PPO Policy
- **Status:** accepted
- **When:** 2026-10-26T17:30:00+07:00
- **Decided by:** human
- **Trigger:** "cải thiện tiếp model train full lên để có RL phiên bản mạnh nhất ! ... làm cái bệnh viện có cái cửa ra vào từ bên ngoài và thường robot sẽ xuất phát ở đó."
- **Decision:**
  1. **Main entrance + robot dock (`room.tscn`):** West end of the floor-1 corridor now has a sliding door ("LỐI VÀO CHÍNH") with a canopy, an outdoor plaza and a sign. `SlidingDoor.robot_can_open = false`: people open it, the robot treats it as a wall, so it never leaves the building. `Entrance/RobotDock` sits at (-10.6, 0) facing the corridor. In Godot every shift starts at the dock; training starts there in 75% of episodes (`DOCK_START_PROB`) and mid-shift elsewhere otherwise. `tools/export_nav_layout.gd` exports the dock and the entrance door (and skips Area3D trigger shapes).
  2. **Geodesic navigation (`hospital_env.NavGrid`):** Replaces the hand-written door/corridor routing. A 0.2 m grid of walls and furniture is inflated by the robot radius (0.34 m). Cells closer than 0.8 m to an obstacle cost up to 4x, so paths keep to the middle of passages. Dijkstra distance fields are cached per target. The sub-goal is the farthest point up to 2 m along the path that is in straight-line sight with at least 0.55 m clearance. Observation `obs[25]` is the remaining path length, and progress shaping and the stagnation clock use path length, so detours around furniture are no longer punished. `rl_policy_server.py` calls the same `set_nav_target()`, and training observations are now rebuilt at the end of each step exactly like the server builds them (no stale sub-goal).
  3. **NPC behaviour (Python env and `hospital_npc.gd`):**
     - NPCs only side-step when they actually block the robot's lane (0.75 m), to 0.8 m off its line.
     - They never cross in front of the robot, and never pick a side-step spot within 1.2 m of a doorway.
     - A side-step is abandoned after 4 s, with a 3 s cooldown before the next one.
     - NPCs never step within 0.9 m of the robot. A patrolling NPC kept waiting for 2 s turns back to its other waypoint.
     - The robot can always back out of an NPC that walked into it.
     - These rules fix the doctor and robot deadlocks in front of room 110.
  4. **Sim/train parity:**
     - Godot patient spawns use the training regions: 60% corridor, 40% lobby, on the robot's floor (`Room.get_patient_spawn_position`).
     - CALL_STAFF targets the nearest nurse or doctor in both Godot and Python.
     - When the staff member is on another floor, the robot rides the elevator alone.
     - The Godot stagnation timer also covers SEARCH/APPROACH (it previously looped forever) and measures progress toward the elevator for cross-floor legs.
     - NLU targets `room_<n>` and `dept_<slug>` are normalized in `RLEnvBridge`. Previously every "phòng XXX" request fell back to the reception desk.
  5. **Training protocol:**
     - Round 1: 4 runs (3 fine-tunes from the previous full model plus 1 from scratch with teacher BC).
     - Round 2: 4 fine-tunes from the round-1 bests on the final env, evaluated every 500 episodes on 100 held-out seeds, with early stopping (patience 20).
     - Every new `best.pt` was snapshotted (`experiments/checkpoints/round2/`).
     - Selection used a separate 1000-seed test on fresh seeds (base 500,000,000) never used in training or best.pt selection.
  6. **Chosen model:** round-2 run A, episode 16000 → `experiments/checkpoints/PPOHospital-full_strongest.pt`. It is now the default checkpoint of `rl_policy_server.py` and `run_simulation.py --controller rl`.
- **Why:** The previous policy stalled behind furniture (about 5% of shifts stuck) because routing was heuristic and shaping was Euclidean. Godot also spawned patients where training never did. A sliding-door start at the entrance matches how a hospital guide robot is actually deployed.
- **Touches:** `src/training/hospital_env.py`, `src/training/hospital_layout.json`, `src/training/train_solo_patient.py` (checkpoint names `PPOHospital-<env_mode>_*.pt`), `sim_vision/python/rl_policy_server.py`, `run_simulation.py`, `sim_vision/godot/scenes/room.tscn`, `sim_vision/godot/scripts/{main,room,sliding_door,hospital_npc,human,rl_env_bridge,view_overlay}.gd`, `sim_vision/godot/tools/export_nav_layout.gd`, `tests/test_nav_layout.py`, `sim_vision/godot/tests/{test_room,test_main,test_sliding_door,test_rl_env}.gd`
- **Evidence:** 1000 fresh seeds, full mode (8 NPCs), deterministic policy:

  | Model | Tasks / shift | Collisions / shift | Zero-collision shifts | Stuck | Score (R_team − collisions) |
  |---|---|---|---|---|---|
  | Previous full model (`20261025_225529…/PPOHospital-solo_best.pt`) | 3.71 | 0.62 | 86.6% | 5.0% | 110.6 |
  | **Strongest (round 2 A, ep 16000)** | **4.02** | 0.89 | 85.4% | **0.0%** | **120.7** |
  | Round 2 D, ep 6000 | 4.05 | 1.18 | 84.0% | 0.0% | 120.7 |
  | Round 2 C, ep 19500 | 4.04 | 1.05 | 83.6% | 0.0% | 120.7 |
  | Round 2 B, ep 1000 (fewest collisions) | 3.97 | 0.65 | 88.4% | 0.2% | 119.2 |

  In solo mode (500 seeds) the strongest model reaches 3.91 tasks, 0.09 collisions and 0% stuck, against 3.61, 0.18 and 3.2% for the previous model. Python tests 30/30 and Godot GUT tests 157/157 pass. An 8-minute Godot full-mode run produced 32 task events with no stuck aborts. It covered answers, a staff call, escorts that reached their destination, and an elevator escort from floor 1 to the floor-2 lobby, after which the robot kept serving patients on floor 2.
