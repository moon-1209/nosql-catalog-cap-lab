# Tuan Decision Log — AI-Assisted Architecture Records

- **Motivation/Background**: Captures architectural, toolchain, and model selection choices made during AI-assisted development to ensure long-term auditability and prevent unrecorded drift.
- **Purpose**: Maintain an immutable, attributable provenance log of decisions for the hospital navigation robot project.
- **Overview Pipeline**: Follows the decision log convention defined in `agents/templates/DECISION_LOG_TEMPLATE.md` and metadata header rules in `agents/rules/MD_CONVENTION.md`.
- **Detailed Plan**: §1 Decision Index Table; §2 Decision Log Entries (D-016 to D-022).
- **References**: [agents/templates/DECISION_LOG_TEMPLATE.md](../../agents/templates/DECISION_LOG_TEMPLATE.md), [agents/rules/MD_CONVENTION.md](../../agents/rules/MD_CONVENTION.md), [docs/AI-Human-logs/Vuong.md](Vuong.md).
- **Created**: 2026-10-22T11:45:00+07:00
- **Last Updated**: 2026-10-22T13:48:00+07:00

---

## 1. Decision Index

| ID | Title | Decided by | Status |
| :--- | :--- | :--- | :---: |
| [D-016](#d-016--create-dedicated-fixcamera-views-branch-for-simulation-viewport-defects) | Create dedicated fix/camera-views branch for simulation viewport defects | human | accepted |
| [D-017](#d-017--dynamically-toggle-ceiling-mesh-visibility-on-top-down-camera) | Dynamically toggle ceiling mesh visibility on TOP_DOWN camera view | agent-proposed, human-approved | superseded by D-020 |
| [D-018](#d-018--recalibrate-lobby-camera-viewpoint-for-expanded-floor-1-hospital) | Recalibrate LOBBY camera viewpoint for expanded Floor-1 hospital layout | agent-proposed, human-approved | accepted |
| [D-019](#d-019--add-automated-camera-mode-and-ceiling-visibility-gut-unit-test) | Add automated camera mode and ceiling visibility GUT unit test | agent-proposed, human-approved | accepted |
| [D-020](#d-020--hide-ceiling-mesh-for-all-spectator-views-to-prevent-follow-mode-white-screen) | Hide ceiling mesh for all spectator views to prevent FOLLOW mode white screen | agent-proposed, human-approved | superseded by D-021 |
| [D-021](#d-021--restore-ceiling-for-followlobby-modes-lower-follow-camera-under-ceiling-and-reframe-top_down) | Restore ceiling for FOLLOW/LOBBY modes, lower FOLLOW camera under ceiling, and reframe TOP_DOWN | agent-proposed, human-approved | accepted |
| [D-022](#d-022--dynamic-see-through-transparency-for-occluding-interior-walls) | Dynamic see-through transparency for occluding interior walls (Option 2B) | human-chosen, agent-implemented | accepted |

---

## 2. Decision Log Entries

### D-016 — Create dedicated fix/camera-views branch for simulation viewport defects
- **Status:** accepted
- **When:** 2026-10-22T11:49:19+07:00
- **Decided by:** human
- **Trigger:** "tạo 1 bracnh mới và fix lỗi này đi"
- **Decision:** Branch off from `feat/hospital-env` into `fix/camera-views` to isolate viewport defect fixes rather than committing directly to `feat/hospital-env` or `main`.
- **Why:** Maintains clean branch hygiene and isolates viewport fixes for regression testing before merging back into `feat/hospital-env`.
- **Rejected:** Committing directly onto `feat/hospital-env` without branch isolation.
- **Touches:** `git branches`
- **Evidence:** `git checkout -b fix/camera-views` created and verified clean.

### D-017 — Dynamically toggle ceiling mesh visibility on TOP_DOWN camera
- **Status:** superseded by D-020
- **When:** 2026-10-22T11:51:32+07:00
- **Decided by:** agent-proposed, human-approved
- **Trigger:** "vậy fix đi"
- **Decision:** Dynamically toggle `ceiling_mesh.visible = (camera_mode != CameraMode.TOP_DOWN)` on camera mode update in `main.gd`, while keeping `CeilingCollision` active for physics.
- **Why:** At `TOP_DOWN` (Y=19.5m), the solid opaque ceiling at Y=3.3m obscured the entire 24m x 18m interior into a giant white polygon. Toggling visibility on the MeshInstance3D preserves all physics collision and lighting.
- **Rejected:** Moving top-down camera below ceiling (Y < 3.2m) — severely restricts top-down FOV and cannot view the full hospital layout simultaneously.
- **Touches:** `sim_vision/godot/scripts/main.gd`
- **Evidence:** Godot viewer verified; ceiling hides in TOP_DOWN and restores in FOLLOW/LOBBY.

### D-018 — Recalibrate LOBBY camera viewpoint for expanded Floor-1 hospital
- **Status:** accepted
- **When:** 2026-10-22T11:51:32+07:00
- **Decided by:** agent-proposed, human-approved
- **Trigger:** "vậy fix đi"
- **Decision:** Recalibrate `LOBBY` camera viewpoint from legacy `(-4.8, 2.85, 8.2)` looking at `(0.0, 1.0, 2.0)` to `Vector3(-4.0, 2.7, 7.8)` looking at `Vector3(0.0, 1.2, 5.0)`.
- **Why:** The legacy coordinate was clipped behind the new partition walls and wheelchair props in the expanded hospital environment. The new coordinates frame the reception counter, waiting benches, and central hallway clearly.
- **Rejected:** Leaving legacy single-room camera coordinates in the multi-room hospital environment.
- **Touches:** `sim_vision/godot/scripts/main.gd`
- **Evidence:** GUT unit test asserts viewer camera position and look target in LOBBY mode.

### D-019 — Add automated camera mode and ceiling visibility GUT unit test
- **Status:** accepted
- **When:** 2026-10-22T11:57:05+07:00
- **Decided by:** agent-proposed, human-approved
- **Trigger:** "kiểm tra và xem đã fix hoàn chỉnh chưa + check toàn bộ project để bổ sung .md cho tôi ở Tuan.md hoặc .md trong folder docs"
- **Decision:** Implement `test_camera_mode_cycles_and_toggles_ceiling` inside `sim_vision/godot/tests/test_main.gd` verifying all 3 camera modes and state transitions.
- **Why:** Eliminates regression risk by systematically testing ceiling visibility flags and camera position coordinates across all camera cycles.
- **Rejected:** Manual inspection only without automated CI assertion.
- **Touches:** `sim_vision/godot/tests/test_main.gd`
- **Evidence:** `godot --headless --path sim_vision/godot -s addons/gut/gut_cmdln.gd -gdir=res://tests` passes 142/142 tests (10,920 asserts).

### D-020 — Hide ceiling mesh for all spectator views to prevent FOLLOW mode white screen
- **Status:** superseded by D-021
- **When:** 2026-10-22T12:15:00+07:00
- **Decided by:** agent-proposed, human-approved
- **Trigger:** "góc này vẫn màu trắng là sao nhỉ"
- **Decision:** Unconditionally hide `ceiling_mesh.visible = false` in `_update_viewer_camera()` for all 3 spectator viewer modes (`FOLLOW`, `TOP_DOWN`, `LOBBY`), keeping collision and robot viewport intact.
- **Why:** The spectator `FOLLOW` camera is at height `Y = 4.2m`, while the hospital ceiling is at `Y = 3.3m`. Restoring the ceiling in `FOLLOW` caused the camera to sit outside above the roof looking down, creating an 83.2% solid white screen. Spectator cameras never need an opaque ceiling blocking the view into hospital rooms.
- **Rejected:** Lowering `FOLLOW` camera below 3.0m without ceiling hiding — still prone to clipping through 3.2m partition walls when robot maneuvers through doorways.
- **Touches:** `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/tests/test_main.gd`
- **Evidence:** Frame captures verified across 5 random seeds (0 to 4) with white pixel percentage dropping from 83.2% down to 2.8%–15.0%; 142/142 GUT tests pass.

### D-021 — Restore ceiling for FOLLOW/LOBBY modes, lower FOLLOW camera under ceiling, and reframe TOP_DOWN
- **Status:** accepted
- **When:** 2026-10-22T13:25:00+07:00
- **Decided by:** agent-proposed, human-approved
- **Trigger:** "fix the camera again on view 1 it too light and dont have celling; and the full view is too far"
- **Decision:**
  1. Restore ceiling mesh visibility for indoor spectator modes (`FOLLOW` and `LOBBY`), only hiding ceiling in `TOP_DOWN` mode (`ceiling_mesh.visible = (camera_mode != CameraMode.TOP_DOWN)`).
  2. Lower `CameraMode.FOLLOW` camera viewpoint from `Y = 4.2m` down into the room at `Y = 2.0m` (safely below the 3.2m ceiling) with boundary clamping `X in [-11.5, 11.5]`, `Y in [0.8, 2.8]`, `Z in [-8.5, 8.5]`. With the ceiling physically present, the interior is naturally shielded from the outdoor sun (`light_energy = 1.8`) and sky ambient light, eliminating the washed-out overexposure ("too light") while keeping the ceiling visible above.
  3. Lower `CameraMode.TOP_DOWN` height from `19.5m` down to `13.0m` (`Vector3(0.0, 13.0, 1.2)` looking at `(0, 0, 0)`), providing optimal framing for the 24m × 18m hospital layout without excessive distant void space ("full view is too far").
- **Why:** Hiding the ceiling unconditionally in D-020 caused sunlight and ambient sky bounce (SDFGI) to flood the interior, bleaching the scene and removing the ceiling entirely from view. The previous white screen was caused by the camera floating above the roof looking down onto the ceiling surface. Placing the camera inside the room at Y = 2.0m under the ceiling solves both the ceiling presence and indoor lighting fidelity. Reframing TOP_DOWN to Y = 13.0m fills the screen with the floor plan instead of wasting space.
- **Rejected:** Keeping ceiling hidden or only lowering TOP_DOWN without fixing FOLLOW ceiling and height.
- **Touches:** `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/tests/test_main.gd`
- **Evidence:** `godot --headless --path sim_vision/godot -s addons/gut/gut_cmdln.gd -gdir=res://tests` passes 142/142 tests (10,922 asserts).

### D-022 — Dynamic see-through transparency for occluding interior walls
- **Status:** accepted
- **When:** 2026-10-22T13:48:00+07:00
- **Decided by:** human-chosen, agent-implemented
- **Trigger:** "if camera is behind the wall cannot see a robot the camera can be able to see through the wall ?" / "option 2B"
- **Decision:** Implement dynamic wall transparency (Option 2B) in `sim_vision/godot/scripts/main.gd`. Whenever any interior partition wall lies between the spectator camera and the robot, dynamically set `material_override` on that wall's `MeshInstance3D` to a semi-transparent material (`transparency = TRANSPARENCY_ALPHA`, alpha = 0.22). When the line of sight clears or the camera switches to `TOP_DOWN`, reset `material_override = null` to restore full opacity.
- **Why:** When the robot maneuvers into a room or behind a divider wall, an opaque wall blocks the user's view of the robot. Option 2B lets the spectator continuously track the robot through walls like in isometric RPGs/Sims without altering physics collisions or moving the camera abruptly.
- **Rejected:** Option 1 (raycast spring arm pushing camera closer) — user explicitly selected Option 2B.
- **Touches:** `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/tests/test_main.gd`
- **Evidence:** Unit test `test_wall_transparency_when_occluded` passes; 143/143 GUT tests pass (10,928 asserts).
