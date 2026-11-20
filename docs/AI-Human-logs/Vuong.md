# Vuong Decision Log — AI-Assisted Architecture Records

- **Motivation/Background**: Captures architectural, toolchain, and model selection choices made during AI-assisted development to ensure long-term auditability and prevent unrecorded drift.
- **Purpose**: Maintain an immutable, attributable provenance log of decisions for the hospital navigation robot project.
- **Overview Pipeline**: Follows the decision log convention defined in `agents/templates/DECISION_LOG_TEMPLATE.md` and metadata header rules in `agents/rules/MD_CONVENTION.md`.
- **Detailed Plan**: §1 Decision Index Table; §2 Decision Log Entries (D-001 to D-039).
- **References**: [agents/templates/DECISION_LOG_TEMPLATE.md](../../agents/templates/DECISION_LOG_TEMPLATE.md), [agents/rules/MD_CONVENTION.md](../../agents/rules/MD_CONVENTION.md).
- **Created**: 2026-10-21T21:25:00+07:00
- **Last Updated**: 2026-10-30T07:00:00+07:00

---

## 1. Decision Index

| ID                                                                                                           | Title                                                                                          | Decided by                     |  Status  |
| :----------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------- | :----------------------------- | :------: |
| [D-001](#d-001--unify-python-dependencies-into-root-venv)                                                     | Unify Python dependencies into root .venv                                                      | human                          | accepted |
| [D-002](#d-002--store-full-phoasr-whisper-small-model-offline)                                                | Store full PhoASR-whisper-small model offline under models/                                    | human                          | accepted |
| [D-003](#d-003--exclude-large-model-weights-from-git-tracking)                                                | Exclude large model weights (>100MB) from Git tracking                                         | human                          | accepted |
| [D-004](#d-004--enable-pytorch-cuda-acceleration-on-rtx-4060)                                                 | Enable PyTorch CUDA acceleration on RTX 4060 GPU                                               | human                          | accepted |
| [D-005](#d-005--standardize-speech-audio-to-16khz-mono-pcm-wav)                                               | Standardize speech audio to 16kHz mono PCM WAV via PyAV                                        | agent-proposed, human-approved | accepted |
| [D-006](#d-006--initialize-godot-project-cache-and-asset-imports-via-headless-editor)                         | Initialize Godot project cache and asset imports via headless editor                           | agent-proposed, human-approved | accepted |
| [D-007](#d-007--cross-platform-windows-path-handling-in-godot-runlogger-tests)                                | Cross-platform Windows path handling in Godot RunLogger tests                                  | agent-proposed, human-approved | accepted |
| [D-008](#d-008--instantiate-folder-structure-rule-from-template)                                              | Instantiate FOLDER_STRUCTURE.md constitutional rule from template                              | agent-proposed, human-approved | accepted |
| [D-009](#d-009--download-and-locate-yolov8n-weights-locally)                                                  | Download and locate yolov8n.pt weights locally under models/                                   | agent-proposed, human-approved | accepted |
| [D-010](#d-010--confirm-fsm-proportional-controller-as-pre-rl-baseline)                                       | Confirm FSM proportional controller as pre-RL baseline                                         | human                          | accepted |
| [D-011](#d-011--document-godot-and-yolo-execution-manual-in-root-readmemd)                                    | Document Godot and YOLO execution manual in root README.md                                     | human                          | accepted |
| [D-012](#d-012--unified-simulation-launcher-and-websocket-send-resilience)                                    | Unified simulation launcher and WebSocket send resilience                                      | human                          | accepted |
| [D-013](#d-013--offline-tts-architecture-and-graceful-subtitle-fallback)                                      | Offline TTS architecture and graceful subtitle fallback                                        | human                          | accepted |
| [D-014](#d-014--expansion-to-floor-1-vietnamese-hospital-environment)                                         | Expansion to Floor-1 Vietnamese hospital environment (24m x 18m)                               | human                          | accepted |
| [D-015](#d-015--hospital-room-enrichment-medical-pedal-waste-bins-and-refined-collisions)                     | Hospital room enrichment, medical pedal waste bins, and refined collisions                     | human                          | accepted |
| [D-016](#d-016--camera-viewpoint-height-correction-and-automatic-ceiling-culling)                             | Camera viewpoint height correction and automatic ceiling culling                               | agent-proposed, human-approved | accepted |
| [D-017](#d-017--vietnamese-medical-staff-npcs-waiting-patients-and-clinical-facility-props)                   | Vietnamese medical staff NPCs, waiting patients, and clinical facility props                   | human                          | accepted |
| [D-018](#d-018--stt-startup-timeout-resilience-and-rocketbox-surface-material-mapping)                        | STT startup timeout resilience and Rocketbox surface material mapping                          | human                          | accepted |
| [D-019](#d-019--elderly-patient-variants-and-walking-canes-for-old-patient-dominated-hospital)                | Elderly patient variants and walking canes for old-patient-dominated hospital                  | human                          | accepted |
| [D-020](#d-020--implement-phase-1-rl-training-plan-with-shared-team-reward-and-elderly-tether-pacing)         | Implement Phase-1 RL training plan with shared team reward and elderly tether pacing           | human                          | accepted |
| [D-021](#d-021--25-epoch-ppo-training-run-on-cuda-and-10-shift-comprehensive-benchmark)                       | 25-Epoch PPO training run on CUDA and 10-shift comprehensive benchmark                         | human                          | accepted |
| [D-022](#d-022--ad-camera-rotation-and-multi-npc-hospital-speech-support)                                     | A/D camera rotation and multi-NPC hospital speech support                                      | human                          | accepted |
| [D-023](#d-023--fix-seated-patient-arrival-trigger-and-implement-two-stage-doorway-waypoint-navigation)       | Fix seated patient arrival trigger and implement two-stage doorway waypoint navigation         | human                          | accepted |
| [D-024](#d-024--implement-gradio-web-dashboard-for-rl-training-control-live-telemetry-and-history-inspection) | Implement Gradio web dashboard for RL training control, live telemetry, and history inspection | human                          | accepted |
| [D-025](#d-025--fix-godot-3d-patient-escort-speed-and-improve-doorway-navigation-tolerance)                   | Fix Godot 3D patient escort speed and improve doorway navigation tolerance                      | human                          | accepted |
| [D-026](#d-026--contrast-and-readability-overhaul-for-rl-training-dashboard-dark-theme)                       | Contrast and readability overhaul for RL training dashboard dark theme                         | human                          | accepted |
| [D-027](#d-027--fix-subprocess-pipe-buffer-deadlock-and-dynamic-run-dropdown-refresh)                         | Fix subprocess pipe buffer deadlock and dynamic run dropdown refresh                           | AI-pair (Manh + Antigravity)   | accepted |
| [D-028](#d-028--implement-solo-patient-focus-training-environment--godot-3d-solo-mode)                        | Implement Solo Patient Focus training environment & Godot 3D solo mode                          | human                          | accepted |
| [D-029](#d-029--1000-episode-solo-patient-ppo-training-with-45s-early-stagnation-cutoff)                     | 1000-Episode Solo Patient PPO training with 45s early stagnation cutoff                         | human                          | accepted |
| [D-030](#d-030--expand-solo-patient-ppo-training-target-to-5000-episodes)                                    | Expand Solo Patient PPO training target to 5000 episodes                                       | human                          | accepted |
| [D-031](#d-031--hospital-floor-2-expansion-two-way-interactive-elevator-and-multi-floor-rl-navigation) | Hospital Floor 2 expansion, two-way interactive elevator, and multi-floor RL navigation | human-approved via /grill-me | accepted |
| [D-032](#d-032--fix-patient-escort-geometric-deadlock-and-velocity-mismatch-during-inference) | Fix patient escort geometric deadlock and velocity mismatch during inference | human | accepted |
| [D-033](#d-033--natural-patient-navigation-animation-stabilization-t-pose-option-and-multi-npc-dialogue-targeting) | Natural patient navigation, animation stabilization (T-pose option), and multi-NPC dialogue targeting | human | accepted |
| [D-034](#d-034--dynamic-3d-door-labels-and-hospital-department-signage-overhaul) | Dynamic 3D door labels and hospital department signage overhaul | human-approved via /grill-me | accepted |
| [D-035](#d-035--floor-3-hospital-extension-and-multi-floor-dynamic-elevator-navigation) | Floor 3 hospital extension and multi-floor dynamic elevator navigation (X = +100.0m) | human-approved via /grill-me | accepted |
| [D-036](#d-036--robot-inspection-telemetry-hud-panel-with-4-tabbed-progress-bar-visualizations) | Robot inspection telemetry HUD panel with 4-tabbed progress bar visualizations | human-approved via /grill-me | accepted |
| [D-037](#d-037--dedicated-3-floor-patient-escort-ppo-training--distraction-guard) | Dedicated 3-Floor Patient Escort PPO Training & Distraction Guard | human-approved via /grill-me | accepted |
| [D-038](#d-038--escort-only-inference-mode-overlay-hud-escort-label-and-manual-test-hotkey) | Escort-Only inference mode, overlay HUD escort label, and manual test hotkey | human | accepted |
| [D-039](#d-039--fix-solo-patient-targeting-busy-guard-and-dialogue-to-escort-transition) | Fix solo patient targeting, busy guard, and dialogue-to-escort transition | human-approved via /grill-me | accepted |
| [D-040](#d-040--fix-gdscript-stt-tts-connection-property-crash-in-dialogue-turn-completed) | Fix GDScript STT/TTS connection property crash in dialogue turn completed | human-directed log analysis | accepted |
| [D-041](#d-041--fix-escort-patient-trapping-behind-furniture-and-dynamic-trail-pruning) | Fix escort patient trapping behind furniture and dynamic trail pruning | human log observation | accepted |
| [D-042](#d-042--seated-patient-interaction-position-stand-up-transition-and-physics-collision-fix) | Seated patient interaction position, stand-up transition, and physics collision fix | AI-pair (Manh + Antigravity) | accepted |
| [D-043](#d-043--analysis-of-duty-cycle-flaws-oracle-dispatch-vs-visual-rl-and-pure-rl-vision-roadmap) | Analysis of duty cycle flaws, oracle dispatch vs visual RL, and pure visual-search RL roadmap | human-directed inquiry | accepted |
| [D-044](#d-044--grill-me-interview-record-pure-visual-search-rl-architecture-and-new-training-branch) | /grill-me interview record: Pure Visual-Search RL architecture and new training branch | human-approved via /grill-me | accepted |

---

## 2. Decision Log Entries

### D-001 — Unify Python dependencies into root .venv

- **Status:** accepted
- **When:** 2026-10-21T19:52:42+07:00
- **Decided by:** human
- **Trigger:** "we keep sim_vision for now,but use root .venv"
- **Decision:** Keep `sim_vision/` directory structure intact, but execute all Python code and tests exclusively via the single root `.venv`.
- **Why:** Eliminates fragmented virtual environments across subfolders and enables IDEs and pytest to discover dependencies globally.
- **Rejected:** Moving `sim_vision/python/*` into `src/` — deferred by user directive; nested `.venv` in subfolders — breaks IDE discovery.
- **Touches:** `requirements/base.txt`, `requirements/dev.txt`, `pytest.ini`, `sim_vision/README.md`
- **Evidence:** `pytest` executed from root discovers and passes all tests; `sim_vision/python/protocol.py` imports cleanly.

### D-002 — Store full PhoASR-whisper-small model offline under models/

- **Status:** accepted
- **When:** 2026-10-21T20:06:06+07:00
- **Decided by:** human
- **Trigger:** "download me this model inprepare for testing voice to text, but the condition is that not loading it using huggface cache, i want the full model on /models"
- **Decision:** Download all 14 model files directly to `models/PhoASR-whisper-small` and load with `local_files_only=True`.
- **Why:** Guarantees offline self-contained reproducibility and eliminates hidden background downloads to `~/.cache/huggingface`.
- **Rejected:** Default Hugging Face cache directory — explicitly forbidden by user; `git clone` with LFS — creates nested `.git` submodules.
- **Touches:** `models/PhoASR-whisper-small/`, `scripts/download_phoasr.py`
- **Evidence:** `python scripts/download_phoasr.py` downloaded 927.6 MB directly into `models/PhoASR-whisper-small`.

### D-003 — Exclude large model weights from Git tracking

- **Status:** accepted
- **When:** 2026-10-21T20:06:24+07:00
- **Decided by:** human
- **Trigger:** "(Recommended) Ignore large weight binaries (e.g. models/**/*.safetensors...)"
- **Decision:** Add `/models/**/*.safetensors`, `/models/**/*.bin`, `/models/**/*.pt` to `.gitignore` while keeping configs, tokenizers, and docs tracked.
- **Why:** `model.safetensors` is 922.2 MB, which violates GitHub's 100 MB per-file push limit.
- **Rejected:** Ignoring the entire `models/PhoASR-whisper-small` directory — loses versioning for architecture configs and tokenizers.
- **Touches:** `.gitignore`
- **Evidence:** `git status -u` confirms `model.safetensors` is ignored while `config.json` and `tokenizer.json` remain tracked.

### D-004 — Enable PyTorch CUDA acceleration on RTX 4060 GPU

- **Status:** accepted
- **When:** 2026-10-21T20:24:18+07:00
- **Decided by:** human
- **Trigger:** "install the gpu version, but also, install all the dependency in requirements for me"
- **Decision:** Install PyTorch 2.6.0+cu124 with CUDA 12.4 support, configure `torch_dll.pth` for Windows DLL resolution, and inherit user site-packages.
- **Why:** Achieves 0.089x real-time inference on the RTX 4060 GPU (11.2× faster than speech) instead of CPU latency (~5–10s/utterance).
- **Rejected:** CPU-only PyTorch — unacceptable latency for real-time robotic conversational interaction.
- **Touches:** `.venv/pyvenv.cfg`, `.venv/Lib/site-packages/torch_dll.pth`, `requirements/base.txt`
- **Evidence:** `python scripts/evaluate_asr.py` processed 70 samples in 28.19s on `cuda` (NVIDIA GeForce RTX 4060 Laptop GPU).

### D-005 — Standardize speech audio to 16kHz mono PCM WAV via PyAV

- **Status:** accepted
- **When:** 2026-10-21T20:35:47+07:00
- **Decided by:** agent-proposed, human-approved
- **Trigger:** "also, the sample are in .m4a, is it the standard format for TTS? if not then convert it"
- **Decision:** Convert all raw `.m4a` files to 16kHz mono 16-bit PCM WAV in `data/processed/real_voice/` using PyAV with corrupt-packet tolerance.
- **Why:** Raw `.m4a` files have header anomalies causing standard loaders to fail; 16kHz mono PCM WAV is the universal standard for Whisper/ASR.
- **Rejected:** Processing raw `.m4a` directly without conversion — failed with `avcodec_send_packet()` on initial packet.
- **Touches:** `scripts/convert_audio.py`, `data/processed/real_voice/*.wav`
- **Evidence:** `python scripts/convert_audio.py` successfully converted all 70 `.m4a` files in 4.0s without data loss.

### D-006 — Initialize Godot project cache and asset imports via headless editor

- **Status:** accepted
- **When:** 2026-10-21T21:26:00+07:00
- **Decided by:** agent-proposed, human-approved
- **Trigger:** "Parse Error: Identifier 'Config' not declared in the current scope" on initial Godot launch
- **Decision:** Execute `godot --headless --editor --quit --path sim_vision/godot` on initial repository setup.
- **Why:** Godot 4 requires the editor scan to build `.godot/global_script_class_cache.cfg` and convert raw textures/models into `.ctex` and `.res` formats. Without this, class names cannot be resolved.
- **Rejected:** Manually writing `.godot/global_script_class_cache.cfg` — fragile, engine-version specific.
- **Touches:** `sim_vision/godot/.godot/`, `README.md`
- **Evidence:** All 81 GUT tests passed after running headless editor import.

### D-007 — Cross-platform Windows path handling in Godot RunLogger tests

- **Status:** accepted
- **When:** 2026-10-21T21:32:00+07:00
- **Decided by:** agent-proposed, human-approved
- **Trigger:** `test_unwritable_path_reports_once_and_keeps_running` failed on Windows with C++ engine error `Could not create directory '/'`.
- **Decision:** Check `OS.get_name() == "Windows"` and use `"C:/"` instead of POSIX `"/"` for read-only directory testing.
- **Why:** On Windows, `"/"` is an invalid drive syntax that triggers Godot engine internal errors, whereas `"C:/"` is an existing root that is write-protected for non-elevated user processes.
- **Rejected:** Skipping the test on Windows — reduces test coverage across developer OS environments.
- **Touches:** `sim_vision/godot/tests/test_run_logger.gd`
- **Evidence:** Test passed with zero unexpected engine errors.

### D-008 — Instantiate FOLDER_STRUCTURE.md constitutional rule from template

- **Status:** accepted
- **When:** 2026-10-21T21:29:00+07:00
- **Decided by:** agent-proposed, human-approved
- **Trigger:** Root smoke test `test_smoke.py::test_documentation_files_exist` failed looking for `agents/rules/FOLDER_STRUCTURE.md`.
- **Decision:** Copy `agents/templates/CREATE_FOLDER_STRUCTURE_TEMPLATE.md` to `agents/rules/FOLDER_STRUCTURE.md`.
- **Why:** Restores the mandatory constitutional folder layout rule and ensures repository conforms to smoke test specifications.
- **Rejected:** Removing the assertion from `test_smoke.py` — violates rule governance integrity.
- **Touches:** `agents/rules/FOLDER_STRUCTURE.md`
- **Evidence:** `pytest` smoke test passes (44/44 tests passed).

### D-009 — Download and locate yolov8n.pt weights locally under models/

- **Status:** accepted
- **When:** 2026-10-21T21:28:00+07:00
- **Decided by:** agent-proposed, human-approved
- **Trigger:** `yolo_server.py` threw `ERROR: model file not found: yolov8n.pt` and exited.
- **Decision:** Download `yolov8n.pt` (6.2 MB) to `models/yolov8n/yolov8n.pt` and place copy at `sim_vision/python/yolov8n.pt`.
- **Why:** `yolo_server.py` strictly prevents automatic runtime downloads by Ultralytics to ensure reproducible, offline execution.
- **Rejected:** Allowing Ultralytics to auto-download at runtime — explicitly prohibited by project specification (`docs/PROMPT/godot_robot_yolo_prompt.md`).
- **Touches:** `models/yolov8n/yolov8n.pt`, `sim_vision/python/yolov8n.pt`
- **Evidence:** Server starts cleanly and processes frames with 165ms inference latency.

### D-010 — Confirm FSM proportional controller as pre-RL baseline

- **Status:** accepted
- **When:** 2026-10-21T21:36:00+07:00
- **Decided by:** human
- **Trigger:** "it still not RL right? the moving is coded?"
- **Decision:** Confirm that current `controller.gd` is an intentional heuristic / proportional (P) FSM baseline, maintaining an isolated `step()` interface.
- **Why:** Phase 1 establishes the perception bridge and logs ground truth dataset (`sim_vision/logs/run_*.csv`). The clean `step(state, dets, time_since_seen_s)` interface allows direct drop-in replacement by `RLController` (via Godot RL Agents / Stable-Baselines3) in Phase 2.
- **Rejected:** Embedding RL dependencies before establishing simulator ground truth and camera perception pipeline.
- **Touches:** `sim_vision/godot/scripts/controller.gd`, `sim_vision/README.md`
- **Evidence:** Controller successfully navigates between `SEARCH`, `APPROACH`, and `ARRIVED` states using proportional control laws.

### D-011 — Document Godot and YOLO execution manual in root README.md

- **Status:** accepted
- **When:** 2026-10-21T21:40:00+07:00
- **Decided by:** human
- **Trigger:** "wait before that, in README.md documented details on how to start the running of godot and such, model/files to download, command to run"
- **Decision:** Expand root `README.md` to include detailed instructions on downloading model weights (YOLOv8n & PhoASR), running the WebSocket server, launching Godot 3D, and executing tests.
- **Why:** The root `README.md` serves as the central portfolio entry point and execution manual for any human engineer or AI agent cloning the repository.
- **Rejected:** Keeping instructions scattered only in `sim_vision/README.md` — causes developer confusion on initial checkout.
- **Touches:** `README.md`
- **Evidence:** `README.md` updated with exact commands for Windows PowerShell and Linux/macOS.

### D-012 — Unified simulation launcher and WebSocket send resilience

- **Status:** accepted
- **When:** 2026-10-22T07:50:00+07:00
- **Decided by:** human
- **Trigger:** "unififle evreything to run to 1 command/ scripts, because as it right now, i have to run command in 3 sperated tab, and its error prone. WARNING: VisionClient: send failed: Failed"
- **Decision:** Create `run_simulation.py` and `run.ps1` at repo root that orchestrate YOLO (8765), STT/NLU (8766), and Godot with health polling and automatic process cleanup. Guard `_send_frame` in `vision_client.gd` with ready-state verification and clean reconnection on send failures.
- **Why:** Running 3 separate terminal tabs manually is prone to human error and orphaned processes on abort. The launcher verifies that WebSocket servers are actively accepting connections before booting Godot, and terminates all child processes when Godot exits.
- **Rejected:** Running complex Docker Compose stacks on local development machine — incompatible with Godot 3D Vulkan rendering without specialized passthrough.
- **Touches:** `run_simulation.py`, `run.sh`, `run.ps1`, `run.bat`, `.gitattributes`, `sim_vision/godot/scripts/vision_client.gd`, `README.md`
- **Evidence:** `run.sh` (Linux/macOS) and `run.ps1` (Windows) boot all backend servers, verify ports via WebSocket ping, launch Godot across Windows/macOS/Linux paths, and cleanly terminate background servers on exit; 135/135 GUT tests pass.

### D-013 — Offline TTS architecture and graceful subtitle fallback

- **Status:** accepted
- **When:** 2026-10-22T07:55:00+07:00
- **Decided by:** human
- **Trigger:** "Do we have implemet TTS yet? i see the TTS status are disable"
- **Decision:** Document and maintain the offline VieNeu-TTS v3 Turbo subsystem (port 8767) with graceful degradation to 4-second on-screen subtitles when the TTS server or model weights are offline.
- **Why:** Large ONNX speech synthesis weights (~2GB) should remain optional so developers without high storage or specific TTS requirements can still test and run full vision and STT navigation simulation.
- **Rejected:** Hard-failing the simulation when TTS server is unreachable — degrades usability for vision and navigation testing.
- **Touches:** `sim_vision/godot/scripts/tts_client.gd`, `sim_vision/godot/scripts/robot_voice.gd`, `sim_vision/python/tts/tts_engine.py`, `scripts/download_tts.py`, `run_simulation.py`, `docs/guide.md`
- **Evidence:** `scripts/download_tts.py` downloaded VieNeu-TTS v3 Turbo ONNX weights & MOSS codec into `models/`; `vieneu` initialized with 25 preset Vietnamese voices; all 3 servers (YOLO 8765, STT 8766, TTS 8767) launched and connected successfully in unified launcher.

### D-014 — Expansion to Floor-1 Vietnamese hospital environment (24m x 18m)

- **Status:** accepted
- **When:** 2026-10-22T08:50:00+07:00
- **Decided by:** human
- **Trigger:** "/plan we are planing to expand on the virtural env for our RL sim_vision\\godot, i want you to first understand the current godot, like assets, can you find more hospital related assets that match our Vietnameses style hospital? -make more room, that statisfiles standard hospital -use slide door, that embed between walls, auto open, so that its not complicate our env, thinks of it like the door in rim worlds /grill-me/grill-me"
- **Decision:** Expand simulator from a single `8 m × 6 m` room to a `24 m × 18 m` (ceiling `3.2 m`) Floor-1 Vietnamese hospital with 6 rooms matching `hospital_map.json` (Emergency 101, Blood Lab 110, Internal Medicine 112, Pharmacy, Main Reception Lobby, Elevator & WC) linked by a central East-West corridor. Implement RimWorld-style pocket sliding doors embedded in 0.2m walls with immediate collision disabling upon trigger area entry to ensure collision-free RL raycasts and movement. Replace foreign fire equipment with authentic Vietnamese PCCC (114) station. Add camera mode switcher (`C` key: `FOLLOW`, `TOP_DOWN`, `LOBBY`).
- **Why:** Provides a realistic multi-room navigation environment with authentic Vietnamese hospital visual cues and structured waypoints for upcoming RL navigation and voice guidance benchmark tasks.
- **Rejected:** Physics-swinging hinged doors — prone to trapping the differential drive robot or causing physics jitter in navigation rays.
- **Touches:** `sim_vision/godot/scenes/room.tscn`, `sim_vision/godot/scripts/room.gd`, `sim_vision/godot/scenes/props/sliding_door.tscn`, `sim_vision/godot/scripts/sliding_door.gd`, `sim_vision/godot/scenes/props/pccc_station.tscn`, `sim_vision/godot/scenes/props/hospital_bed.tscn`, `sim_vision/godot/scenes/props/waiting_bench.tscn`, `sim_vision/godot/scenes/props/reception_counter.tscn`, `sim_vision/godot/scenes/props/hospital_sign.tscn`, `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/scenes/main.tscn`, `sim_vision/godot/tests/test_room.gd`, `sim_vision/godot/tests/test_sliding_door.gd`, `sim_vision/godot/tests/test_main.gd`
- **Evidence:** Dedicated branch `feat/hospital-env` verified with 141/141 passing GUT unit tests.

### D-015 — Hospital room enrichment, medical pedal waste bins, and refined collisions

- **Status:** accepted
- **When:** 2026-10-22T09:25:00+07:00
- **Decided by:** human
- **Trigger:** "commits then update 1. some of the rooms lack so much things, add more stuff to it 2. the trash bin looks ugly, that is the kind of bin that been deprecated long ago (i delelte it)and not suitable for hospital env, find the better model 3. i ajust some collision box for better match and moving object"
- **Decision:** Delete deprecated corrugated metal street trash bin (`metal_trash_can`) and replace it with Vietnamese Ministry of Health standard pedal waste bins (`medical_waste_bin.tscn` paired Green domestic + Yellow biohazard bins). Enrich every room with authentic clinical and facility assets (Emergency 101: 3-panel privacy screen, 2 vital signs monitor trolleys with ECG & O2 tanks, supply rack, wheelchair, X-Ray viewer board; Lab 110: optical microscope, chemistry set, phlebotomy desk; Clinic 112: consultation chairs, exam bed privacy screen, vitals trolley; Elevator/WC: double bed-elevator doors with LED indicator, ceramic washbasin vanity with 6-step handwash board & WC stall partition). Preserve human collision box adjustments and assign exact vertex-matched `BoxShape3D` bounds to all models.
- **Why:** Upgrades environment realism to match Vietnamese hospital standards while keeping waypoints clear for robotic navigation and preserving tight collision boundaries.
- **Rejected:** Generic street containers or cluttered non-medical props.
- **Touches:** `sim_vision/godot/scenes/room.tscn`, `sim_vision/godot/scenes/props/medical_waste_bin.tscn`, `sim_vision/godot/scenes/props/medical_trolley.tscn`, `sim_vision/godot/scenes/props/medical_screen.tscn`, `sim_vision/godot/scenes/props/elevator_doors.tscn`, `sim_vision/godot/scenes/props/wc_station.tscn`, `sim_vision/godot/scenes/props/medical_wall_board.tscn`, `scripts/download_hospital_assets.py`, `sim_vision/godot/assets/CREDITS.md`
- **Evidence:** 141/141 tests pass with 10,912 assertions in Godot GUT test suite; committed as `e94381b`.

### D-016 — Camera viewpoint height correction and automatic ceiling culling

- **Status:** accepted
- **When:** 2026-10-22T09:42:00+07:00
- **Decided by:** agent-proposed, human-approved
- **Trigger:** "fix, when tries to run the project, out of 3 view port, only the 1 works, 2 other looks like are too far or such, only see the roof of the hospital"
- **Decision:** Correct camera height and clipping across all 3 view modes: 1) in `FOLLOW` mode, position the camera inside the hospital at height `y = 1.85 m` (under the `3.2 m` ceiling) trailing `2.3 m` behind the robot; 2) in `TOP_DOWN` mode, automatically hide the opaque ceiling mesh (`room.set_ceiling_visible(false)`) so the camera at `y = 18.0 m` has an unobstructed RimWorld-style bird's-eye view into all rooms; 3) in `LOBBY` mode, position the camera at `(-5.0, 2.3, 3.2)` inside the lobby looking across the reception counter, restoring ceiling visibility (`room.set_ceiling_visible(true)`). Update UI help label to reflect active view name dynamically.
- **Why:** Previously, `FOLLOW` was at `y = 4.2 m` and `TOP_DOWN` was at `y = 19.5 m`, both above the opaque ceiling (`y = 3.3 m`), which caused both cameras to view only the external roof.
- **Rejected:** Removing ceiling mesh entirely — ceiling is necessary for first-person robot camera and realistic interior lighting when inside rooms.
- **Touches:** `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/scripts/room.gd`, `sim_vision/godot/tests/test_room.gd`
- **Evidence:** All 142/142 GUT tests pass; all 3 camera modes render interior hospital environments without roof clipping.

### D-017 — Vietnamese medical staff NPCs, waiting patients, and clinical facility props

- **Status:** accepted
- **When:** 2026-10-23T08:40:00+07:00
- **Decided by:** human
- **Trigger:** "hey, add more NPC to our env, 2 medical staff (vietnam style, it can be the variant between doctor or nurse) 4 more patient, most of them waiting in the wainting rooms. Overall, we need more assests"
- **Decision:** Add `HospitalNpc` (`sim_vision/godot/scripts/hospital_npc.gd`) and populate `room.tscn` with 2 Vietnamese-style medical staff (`MedicalStaffNurse` with white nurse cap and blue collar trim at reception, `MedicalStaffDoctor` in white lab coat in the corridor), seated waiting patients on lobby/corridor benches, and 8 hospital prop scenes (`queue_kiosk.tscn`, `queue_display.tscn`, `water_dispenser.tscn`, `sanitizer_stand.tscn`, `vital_monitor.tscn`, `iv_stand.tscn`, `stretcher_cart.tscn`, `info_standee.tscn`).
- **Why:** Increases visual realism and obstacle density in the waiting lobby, corridor, Emergency 101, and Clinic 112 while automatically registering `StaticBody3D` footprints with `Room.get_furniture_footprints()`.
- **Rejected:** Unrigged static mannequins without idle animations — lacks lifelike hospital atmosphere.
- **Touches:** `sim_vision/godot/scripts/hospital_npc.gd`, `sim_vision/godot/scenes/room.tscn`, `sim_vision/godot/scenes/props/npc_medical_nurse.tscn`, `sim_vision/godot/scenes/props/npc_medical_doctor.tscn`, `sim_vision/godot/scenes/props/queue_kiosk.tscn`, `sim_vision/godot/scenes/props/queue_display.tscn`, `sim_vision/godot/scenes/props/water_dispenser.tscn`, `sim_vision/godot/scenes/props/sanitizer_stand.tscn`, `sim_vision/godot/scenes/props/vital_monitor.tscn`, `sim_vision/godot/scenes/props/iv_stand.tscn`, `sim_vision/godot/scenes/props/stretcher_cart.tscn`, `sim_vision/godot/scenes/props/info_standee.tscn`
- **Evidence:** `test_has_medical_staff_and_waiting_patients_and_new_props` in `test_room.gd` passes.

### D-018 — STT startup timeout resilience and Rocketbox surface material mapping

- **Status:** accepted
- **When:** 2026-10-23T10:15:00+07:00
- **Decided by:** human
- **Trigger:** "[Launcher] -> STT Server timed out after 60.0s!" / "the human model is broken"
- **Decision:** Increase `wait_for_port` timeout in `run_simulation.py` from `60.0s` to `180.0s` with early `proc.poll()` crash detection, replace slow `AutoModelForSpeechSeq2Seq` lazy discovery in `transcriber.py` with direct `WhisperForConditionalGeneration` and `WhisperProcessor` imports, and map `HospitalNpc` mesh surfaces dynamically by FBX material name (`body`, `head`, `opacity`) using `TRANSPARENCY_ALPHA_HASH` and `CULL_DISABLED` on the hair/eyelash opacity layer.
- **Why:** Concurrent cold-start loading of YOLOv8, VieNeu-TTS ONNX, and PhoASR-whisper-small exceeded 60s on Windows disk/CUDA initialization. Additionally, Rocketbox FBX meshes order surfaces as `[0: body, 1: head, 2: opacity]`, so hardcoding surface 0 as `head` mapped face textures onto the torso and body textures onto the hair/eyelash transparency layer.
- **Rejected:** Hardcoding surface indices — balding avatars have 2 surfaces while standard avatars have 3 surfaces.
- **Touches:** `run_simulation.py`, `sim_vision/python/voice/transcriber.py`, `sim_vision/python/voice/stt_server.py`, `sim_vision/godot/scripts/hospital_npc.gd`
- **Evidence:** Forward+ viewport renders verified clean facial, clothing, and hair rendering across all NPCs; all 3 servers start and pass health checks.

### D-019 — Elderly patient variants and walking canes for old-patient-dominated hospital

- **Status:** accepted
- **When:** 2026-10-23T10:49:00+07:00
- **Decided by:** human
- **Trigger:** "ok, now add more 2 patent but with model of old people, make a few varient of old patient, our hospital will be old patient dominated"
- **Decision:** Expand seated waiting patients from 4 to 6 (`WaitingPatient1` to `WaitingPatient6`), with 5 distinct elderly patient variants (`npc_patient_f02.tscn` silver-haired woman in white sweater, `npc_patient_elder_m03.tscn` silver-haired man in tweed blazer, `npc_patient_elder_f09.tscn` silver-haired grandmother in brown cardigan, `npc_patient_m05.tscn` white-haired bearded man coughing in corridor, and `npc_patient_elder_m14.tscn` balding senior man) plus 3D wooden walking canes (`has_cane = true` in `HospitalNpc`).
- **Why:** Reflects demographic reality where hospital outpatient waiting rooms are predominantly elderly patients with varied attire, hair, and mobility aids.
- **Rejected:** Duplicating a single elderly model across multiple seats — looks repetitive and artificial.
- **Touches:** `sim_vision/godot/scripts/hospital_npc.gd`, `sim_vision/godot/scenes/room.tscn`, `sim_vision/godot/scenes/props/npc_patient_elder_m03.tscn`, `sim_vision/godot/scenes/props/npc_patient_elder_f09.tscn`, `sim_vision/godot/scenes/props/npc_patient_elder_m14.tscn`, `sim_vision/godot/scenes/props/npc_patient_f02.tscn`, `sim_vision/godot/scenes/props/npc_patient_m05.tscn`, `sim_vision/godot/scenes/props/npc_patient_f08.tscn`, `sim_vision/godot/assets/CREDITS.md`, `sim_vision/godot/tests/test_room.gd`
- **Evidence:** `Godot_v4.7.2-stable_win64_console.exe --headless --path sim_vision/godot -s addons/gut/gut_cmdln.gd -gtest=res://tests/test_room.gd -gexit` passes 145/145 tests (12,928 asserts) across all 14 test suites.

### D-020 — Implement Phase-1 RL Training Plan with Shared Team Reward and Elderly Tether Pacing

- **Status:** accepted
- **When:** 2026-10-23T12:54:00+07:00
- **Decided by:** human-approved via `/grill-me` alignment (`rl_training_plan.md`)
- **Trigger:** "ok, draft up a plan for RL traning, we have 1 agents at first, a share reward of how many times it successful help the patient who in trouble, like asking for a place, a information, etc, ... robot should be able to walk patent to the destination they needed given that the location is appropritate, and answer appropritte question successfull or call for staff."
- **Decision:** Implement Phase-1 RL system:
  1. Add 17-ray horizontal 2D LiDAR fan (`200°` FOV, `6.0 m` range) on `Robot` (`robot.gd`).
  2. Implement `RLEnvBridge` (`rl_env_bridge.gd`) and `RLController` (`rl_controller.gd`) with Smart Floor-1 destination routing (`101`, `110`, `112`, `nha_thuoc`, `tiep_don`, `nha_ve_sinh`, elevator `thang_may` for Floor 2–4 requests, and `staff` for emergency/staff calls), coupled elderly patient tether pacing (`0.48 m/s`, `2.5 m` limit), and shared team reward `R_team` (`+10` verbal answer, `+20` staff call, `+30` escort completed).
  3. Implement Python RL training stack under `src/` following `LOGGING_CHECKPOINT_RULES.md`: `RunLogger` (`src/utils/run_logger.py`), full-state checkpointing with `weights_only=True` (`src/utils/checkpoint_utils.py`), Actor-Critic PPO (`src/models/ppo_agent.py`), fast 24m × 18m simulated shift environment (`src/training/hospital_env.py`), and CLI training entry point (`src/training/rl_hospital_train.py` supporting `--epochs`, `--seed`, `--stage`, `--resume`, `--force-resume`, `--tb`, `--smoke`).
  4. Update `run_simulation.py` with `--controller {fsm,rl}` and `--rl-checkpoint` flags.
- **Why:** Delivers robust, resumable, and safe continuous reinforcement learning for multi-patient hospital shifts while keeping the `R_team` reward function ready for multi-agent expansion without redesign.
- **Rejected:** Monolithic end-to-end policy predicting words/intents from raw camera pixels — fragile, slow to train, and discards existing high-accuracy PhoWhisper/PhoBERT pipeline.
- **Touches:** `sim_vision/godot/scripts/robot.gd`, `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/scripts/rl_env_bridge.gd`, `sim_vision/godot/scripts/rl_controller.gd`, `sim_vision/godot/tests/test_rl_env.gd`, `src/utils/run_logger.py`, `src/utils/checkpoint_utils.py`, `src/models/ppo_agent.py`, `src/training/hospital_env.py`, `src/training/rl_hospital_train.py`, `sim_vision/python/test_rl_hospital.py`, `run_simulation.py`, `docs/RL_TRAINING_PLAN.md`
- **Evidence:** All 5 Godot RL tests in `test_rl_env.gd` passed (81 asserts); all 11 `test_robot.gd` tests passed; all 10 `test_main.gd` tests passed; all 7 Python RL tests in `test_rl_hospital.py` passed (100%); CLI smoke training (`--smoke`), `--resume`, and `--force-resume` verified.

### D-021 — 25-Epoch PPO Training Run on CUDA and 10-Shift Comprehensive Benchmark

- **Status:** accepted
- **When:** 2026-10-23T13:12:00+07:00
- **Decided by:** human-approved via `/grill-me` alignment (`rl_full_training_plan.md`)
- **Trigger:** "Full PPO Training Run & Evaluation (Train Phase-1 agent for 20-30 epochs, generate curves, evaluate metrics)"
- **Decision:** Execute 25-epoch PPO training run on CUDA (`NVIDIA GeForce RTX 4060 Laptop GPU`) with 1,200 steps per epoch across the 2-stage curriculum (Stage 1: epochs 1–10 Lobby/Corridor; Stage 2: epochs 11–25 Full 6-room hospital). Run 10 evaluation shifts per stage, plot training curves to `experiments/plots/rl_training_curves.png`, and publish `experiments/results/rl_hospital/evaluation_report.md`.
- **Why:** Confirms empirical convergence of the PPO policy under realistic multi-shift hospital dynamics, validates elderly patient tether regulation (> 86% compliance in Stage 1, > 71% in Stage 2), and provides publication-grade evaluation curves and checkpoint artifacts.
- **Rejected:** Running on CPU without GPU acceleration — would increase wall-clock training time substantially.
- **Touches:** `src/training/rl_hospital_train.py`, `src/training/benchmark_and_plot.py`, `experiments/results/rl_hospital/evaluation_report.md`, `experiments/results/README.md`, `experiments/plots/rl_training_curves.png`
- **Evidence:** 25-epoch training completed in 250s with best validation $R_{\text{team}} = 27.50$ at Epoch 24; 10-shift benchmark completed with mean $R_{\text{team}} = 41.60 \pm 27.08$ and 11 patient escorts in Stage 2.

### D-022 — A/D Camera Rotation and Multi-NPC Hospital Speech Support

- **Status:** accepted
- **When:** 2026-10-23T13:42:00+07:00
- **Decided by:** human
- **Trigger:** "1. when spectating the robot, add A-D key for camera rotations / 2. it seem that, except from the first ever NPC that we create, no other NPC/patient have the ability to speek"
- **Decision:**
  1. Add 360° camera orbit controls via `A` (orbit left/clockwise) and `D` (orbit right/counter-clockwise) keys in `CameraMode.FOLLOW` spectating mode on `Main` (`main.gd`) with smooth delta integration and keypress stepping, updating HUD help text in `main.tscn`.
  2. Extend `HospitalNpc` (`hospital_npc.gd`) to automatically instantiate `Head/Voice` (`AudioStreamPlayer3D`) and an `Npc` dialogue component, mapping female textures to speaker `B` and male textures to speaker `A`.
  3. Generalize `Npc` (`npc.gd`) to accept generic `Node3D` parents, allowing seated patients to initiate conversation without getting off benches while preserving full walk/rotation logic for walking NPCs.
  4. Upgrade `DialogueManager` (`dialogue_manager.gd`) with multi-NPC registration (`register_npc`, `active_npc`), dynamically tracking whichever patient or medical staff member is currently speaking to the robot.
- **Why:** Enables full rotational inspection of robot locomotion and LiDAR navigation from any spectating angle, and activates voice interactions for all hospital patients and staff rather than just the initial test avatar.
- **Rejected:** Hardcoding camera angles — prevents user from checking blind spots behind doors and obstacles.
- **Touches:** `sim_vision/godot/scenes/main.tscn`, `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/scripts/npc.gd`, `sim_vision/godot/scripts/hospital_npc.gd`, `sim_vision/godot/scripts/dialogue_manager.gd`, `sim_vision/godot/scripts/rl_env_bridge.gd`
- **Evidence:** `test_main.gd` passes 10/10 (328 asserts); `test_dialogue.gd` passes 21/21; `test_human.gd` passes 7/7; `test_rl_env.gd` passes 5/5; `test_room.gd` passes 12/12.

### D-023 — Fix Seated Patient Arrival Trigger and Implement Two-Stage Doorway Waypoint Navigation

- **Status:** accepted
- **When:** 2026-10-23T15:45:00+07:00
- **Decided by:** human
- **Trigger:** "sitting patent still not talk, and the RL pathfinding still bad, do more traninig"
- **Decision:**
  1. Fix Seated Patient Arrival Trigger & Dialogue Initialization:
     - In `Main` (`sim_vision/godot/scripts/main.gd`), update `_apply(cmd)`: when approaching a human and safely halted or within `Config.SAFE_DIST_HUMAN + 0.35` (or when velocity is zeroed at safe distance with bounding box height $h \ge 0.45$), transition `state` to `Config.RobotState.ARRIVED`. This solves the issue where seated patients (whose bounding box height is naturally $\approx 0.50$ vs standing $H_{\text{target}} = 0.85$) left the robot stuck in `APPROACH` with $v = 0.0$.
     - Explicitly pass `func() -> int: return state` to all `HospitalNpc` instances during `_setup_hospital_npcs()` in `main.gd` rather than relying on `get_tree().current_scene`.
     - In `HospitalNpc` (`sim_vision/godot/scripts/hospital_npc.gd`), accept optional `state_fn: Callable` in `setup_robot()`.
     - In `Npc` (`sim_vision/godot/scripts/npc.gd`), in `_process()`, if the robot is approaching within $1.15\,\text{m}$ and stopped ($|v| < 0.05\,\text{m/s}$), safely evaluate `r_state = ARRIVED`, triggering `NOTICE` $\to$ `TALK`.
     - Expand `_nearest_person_distance()` in `main.gd` to check all `HospitalNpc` children in `Furniture` (both seated and standing).
  2. Implement Two-Stage Doorway Sub-Goal Waypoint Navigation for RL:
     - In `RLController` (`sim_vision/godot/scripts/rl_controller.gd`) and `HospitalShiftEnv` (`src/training/hospital_env.py`): Implement `route_through_corridor_goal()` with two-stage doorway crossing:
       a) First steer to the corridor doorway approach point $(door_x, -1.0)$ / $(door_x, 1.0)$.
       b) Second steer across the threshold into the room $(door_x, -2.6)$ / $(door_x, 2.6)$ before targeting destination coordinates deep inside the room.
     - Expand 17-ray LiDAR lookahead repulsion from $0.35\,\text{m}$ to $0.65\,\text{m}$ and add dynamic speed regulation (`speed_factor = clampf(center_min / 0.65, 0.35, 1.0)`), eliminating wall clipping and doorframe snags.
     - Match `teacher_action()` in `hospital_env.py` to provide high-quality safe navigation trajectories during behavior cloning warm-up.
- **Why:** Ensures all hospital patients (especially seated elderly patients on benches) immediately engage in voice dialogue upon robot arrival, and eliminates pathfinding collisions across room doorways.
- **Rejected:** Lowering global $H_{\text{target}}$ to 0.50 — causes robot to stop too far from standing patients ($> 2.5\,\text{m}$).
- **Touches:** `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/scripts/hospital_npc.gd`, `sim_vision/godot/scripts/npc.gd`, `sim_vision/godot/scripts/rl_controller.gd`, `src/training/hospital_env.py`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** 151/151 GUT unit tests passing (13,015 asserts, 0 failures); 30-epoch PPO training run (`PPOHospital-doorway-curriculum`) launched on RTX 4060 GPU with clean doorway clearance.

### D-024 — Implement Gradio Web Dashboard for RL Training Control, Live Telemetry, and History Inspection

- **Status:** accepted
- **When:** 2026-10-23T16:45:00+07:00
- **Decided by:** human-approved via `/grill-me` alignment (`rl_ui_dashboard_plan.md`)
- **Trigger:** "make me a UI that have those funtionality / 1. it can start the trainig either new or contnue from a previous runs, flags can be tick using tick box / 2. when training, its show in realtime, episode, avg reward, times, in grahp etc... / 3. when continuse the previous run, it load the previous run training grahpts, stats etc .."
- **Decision:**
  1. Build a Gradio 6.30 Web Dashboard (`src/ui/rl_dashboard.py`) and single-command launcher (`run_dashboard.py`).
  2. Implement decoupled background subprocess execution (`start_training`, `stop_training`) streaming real-time metrics and logs with clean SIGINT/SIGTERM handling to preserve checkpoints.
  3. Implement historical run inspection and dropdown loader (`find_existing_runs`, `inspect_run`) immediately rendering 4 multi-line charts (Reward, Loss, Productivity, Safety) and KPI cards from any past run under `experiments/runs/`.
  4. Provide tick boxes and intuitive widgets for all training flags (`--device cuda`, `--resume`, `--force-resume`, `--tb`, `--smoke`, `--stage`).
  5. Add Godot 3D quick-launch shortcut to directly spin up `run_simulation.py --controller rl --rl-checkpoint ...` with the selected run's checkpoint.
- **Why:** Replaces manual terminal command typing with a modern visual controller, provides live visual feedback during continuous reinforcement learning, and allows instant comparative inspection of historical training runs without leaving the browser.
- **Rejected:** Native Tkinter GUI (limited modern web-grade charting, desktop-only) or custom full-stack React app (unnecessary engineering overhead when Gradio 6.30 is already installed in root `.venv`).
- **Touches:** `src/ui/rl_dashboard.py`, `run_dashboard.py`, `tests/test_dashboard.py`, `README.md`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** 4/4 automated tests in `tests/test_dashboard.py` passed; `run_dashboard.py --help` verified; all 151 Godot GUT tests pass; verified loading of 80-epoch converged run (`PPOHospital-converged-80ep-full`) with peak $R_{\text{team}} = 103.0$ and 4.0 patients helped/shift.

### D-025 — Fix Godot Vision-Client Inference Error (`robot.v` / `robot.omega` Access)

- **Status:** accepted
- **When:** 2026-10-23T17:00:00+07:00
- **Decided by:** AI-pair (Manh + Antigravity)
- **Trigger:** SCRIPT ERROR during YOLO vision inference in Godot: `Invalid access to property or key 'v' on a base object of type 'CharacterBody3D (Robot)'. at: Main._on_detections (res://scripts/main.gd:359)`
- **Decision:**
  1. Add GDScript property getters and setters for `v` and `omega` on `Robot` in `sim_vision/godot/scripts/robot.gd` mapping cleanly to internal `_v`, `_omega` and `set_command()`.
  2. In `sim_vision/godot/scripts/main.gd:359`, retrieve command via `robot.get_command() if robot.has_method("get_command") else Vector2(robot.v, robot.omega)` for defensive execution during RL guide/escort phase.
- **Why:** Prevents runtime GDScript crashes during YOLO vision inference loops when logging telemetry commands.
- **Touches:** `sim_vision/godot/scripts/robot.gd`, `sim_vision/godot/scripts/main.gd`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** All 151 Godot GUT unit tests pass without error (13,015 asserts, 0 failures).

### D-026 — Revamp Dashboard Dark Theme Contrast and Chart Legibility

- **Status:** accepted
- **When:** 2026-10-23T17:08:00+07:00
- **Decided by:** AI-pair (Manh + Antigravity)
- **Trigger:** "the style of the dashboard need to be make more easy to read, in dark theme i can not see the some number"
- **Decision:**
  1. Refactor Matplotlib styling in `generate_metric_plots` using a high-contrast dark telemetry theme (`#0f172a` figure, `#1e293b` axes, `#f8fafc` titles, `#cbd5e1` tick numbers and labels, `#334155` grid lines, glowing neon curves `#38bdf8`, `#34d399`, `#fb923c`, `#f87171`).
  2. Replace hardcoded light CSS in `src/ui/rl_dashboard.py` with `DASHBOARD_CSS` ensuring KPI numbers are rendered in bold glowing electric cyan (`#38bdf8`) on deep slate card containers (`#0f172a` / `#1e293b`) with crisp silver titles (`#94a3b8`).
  3. Ensure numbers in Gradio sliders, numeric inputs, and textboxes use high-contrast cyan/white fonts (`#38bdf8` / `#f8fafc`) in dark theme.
  4. Inject `DASHBOARD_CSS` directly into the DOM tree via `gr.HTML` and `launch(css=DASHBOARD_CSS)` with 0 warnings.
- **Why:** Resolves washed-out and dark-on-dark invisible numbers in Gradio's dark theme, delivering maximum legibility for all telemetry values, sliders, and charts.
- **Touches:** `src/ui/rl_dashboard.py`, `tests/test_dashboard.py`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** 5/5 pytest tests in `tests/test_dashboard.py` pass cleanly with 0 warnings; all 9/9 repo tests pass.

### D-027 — Fix Subprocess Pipe Buffer Deadlock and Dynamic Run Dropdown Refresh

- **Status:** accepted
- **When:** 2026-10-23T20:36:00+07:00
- **Decided by:** AI-pair (Manh + Antigravity)
- **Trigger:** "i order for 120 epoch, why it stop at 16? I can not even find it in the continuation list experiments\runs\20261023_193057_PPOHospital-interactive"
- **Decision:**
  1. Root cause 1: `start_training` spawned `rl_hospital_train.py` with `stdout=subprocess.PIPE` without draining the OS pipe buffer in Python. After 16 epochs of stdout text, Windows kernel pipe buffer (4–64 KB) filled up and blocked `sys.stdout.write(...)` in kernel `NtWriteFile` (Thread WaitReason: Executive). Fixed by introducing asynchronous daemon reader thread `_drain_stdout` continuously draining lines into `collections.deque(maxlen=300)`.
  2. Root cause 2: `on_mode_change` in `rl_dashboard.py` previously only toggled visibility without re-scanning runs. Fixed by dynamically calling `find_existing_runs()` and updating `run_dropdown` choices, default selection, and auto-invoking `inspect_run` to immediately load charts, KPIs, and checkpoints when switching to "Continue from Previous Run".
  3. Support explicit `--resume-from <dir>` CLI flag in `src/training/rl_hospital_train.py` and pass exact run folder from dashboard.
  4. Updated `find_existing_runs()` to compute peak validation reward across all epochs rather than just the final epoch.
- **Why:** Prevents multi-epoch training deadlocks and ensures all active and past runs are immediately selectable and visible in the continuation UI without requiring server restarts.
- **Touches:** `src/ui/rl_dashboard.py`, `src/training/rl_hospital_train.py`, `tests/test_dashboard.py`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** Verified clean resume of `20261023_193057_PPOHospital-interactive` from epoch 16 to 17; 9/9 pytest tests pass; verified `find_existing_runs` dynamically lists `20261023_193057_PPOHospital-interactive (Ep 16 | Peak R: 53.0 | Help: 0.5)`.


### D-028 — Implement Solo Patient Focus Training Environment & Godot 3D Solo Mode
- **Status:** accepted
- **When:** 2026-10-24T14:12:00+07:00
- **Decided by:** human-approved via `/grill-me` alignment (`rl_solo_patient_env_plan.md`)
- **Trigger:** "make me a training env, in that, each times, there only 1 patient not doctor appear, the robot spawn nearby, its task is to answer patient question, guide them to a destination or call for doctor, the env is the current hospital env, each times a patient problems got resolve, apear another one at random location (that not in the medical room), traning on that, instead of the full hospital with full flesh doctor and many patient"
- **Decision:**
  1. In `src/training/hospital_env.py`: Added `env_mode: str = "solo"` support to `HospitalShiftEnv`. In solo mode:
     - Patrolling doctor dynamic obstacle is completely disabled (`doctor_active = False`).
     - Patients strictly spawn in public hallways/corridors or main lobby (`_sample_patient_spawn_solo()`), never inside medical exam rooms.
     - On episode reset, the robot spawns in close proximity (2.0–3.5 m) facing the patient with direct line of sight.
     - When a patient task completes, the next patient spawns in a random corridor/lobby spot while the robot maintains its current position without teleporting.
     - Task distribution configured to escort-heavy: ~70% Guide/Escort, ~15% Question Answering, ~15% Call Staff/Doctor.
  2. In `src/training/rl_hospital_train.py`: Added `--env-mode {solo, full}` CLI argument (defaulting to `"solo"`), wired through training and validation loops, and saved in run metadata.
  3. In `sim_vision/godot/scripts/main.gd` & `run_simulation.py`: Added `--solo-patient` runtime flag. In solo mode, Godot disables extra scene NPCs/doctors, spawns the robot nearby the patient on reset, and respawns the patient at public waypoints without robot teleportation upon task completion.
  4. In `src/ui/rl_dashboard.py`: Added "🏥 Environment Mode" dropdown selector defaulting to `Solo Patient Focus (1 Patient, Nearby Spawn)` and passed appropriate flags to training and 3D simulation launch commands.
- **Why:** Eliminates multi-NPC navigation distractions during early policy learning, focuses learning capacity on core patient interaction, tethered escorting, and doorway navigation from nearby spawns.
- **Touches:** `src/training/hospital_env.py`, `src/training/rl_hospital_train.py`, `run_simulation.py`, `sim_vision/godot/scripts/main.gd`, `src/ui/rl_dashboard.py`, `tests/test_solo_env.py`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** 4/4 tests in `tests/test_solo_env.py` pass; all 13 repo pytest tests pass; all 151 Godot GUT unit tests pass (13,015 asserts, 0 failures); verified 1-epoch GPU smoke test on RTX 4060 with `--env-mode solo`.


### D-029 — 1000-Episode Solo Patient PPO Training with 45s Early Stagnation Cutoff
- **Status:** accepted
- **When:** 2026-10-24T14:35:00+07:00
- **Decided by:** human-approved via `/grill-me` alignment (`train_solo_1000ep_plan.md`)
- **Trigger:** "train for me 1000 episode, each episode terminate when a certain number of times haves pass and it dont complete anymore task /grill-me monitor in real time via terminal logs when running/grill-me"
- **Decision:**
  1. In `src/training/hospital_env.py`: Added `stagnation_timeout_s: float = 0.0` and `stagnation_penalty: float = -10.0` configuration to `HospitalShiftEnv`. When `stagnation_timeout_s > 0` (45.0s = 225 steps at dt=0.2s), an internal counter `steps_since_task` increments each step and resets to 0 whenever a task is completed (`answer`, `call_staff`, `guide_completed`). If 225 steps elapse without completing any task, the episode immediately terminates (`done = True`, `exit_reason = "STAGNATION_TIMEOUT"`) and applies `-10.0` terminal penalty.
  2. Implemented dedicated trainer `src/training/train_solo_1000ep.py` managing a discrete 1000-episode training loop (Ep 1 to 1000) warm-started from the best converged 80-epoch checkpoint `PPOHospital-converged-80ep-full_best.pt` ($R_{team} = 103.0$).
  3. Action execution blends teacher guidance decaying linearly from `prior_weight = 0.10` to `0.0` over the first 200 episodes.
  4. PPO optimization is batched every 5 episodes (200 updates total) over 4 epochs per batch with AdamW (lr: 1e-4 -> 3e-5 via CosineAnnealingLR) and grad norm clipping 0.5.
  5. Live single-line log flushed to terminal after each episode: `[EP 0142/1000] Tasks: 4 | R_team: +42.0 | Dur: 36.8s (184 stp) | Exit: COMPLETED | Col: 1 | Roll20: +33.5 | Peak: +60.0 | ETA: 28.4m`.
  6. Checkpointing: Saves `PPOHospital-solo-1000ep_best.pt` on rolling-20 reward all-time high and `PPOHospital-solo-1000ep_last.pt` every 50 episodes.
- **Why:** Prevents wasting compute wandering when robot gets stuck or loses tether during solo patient interaction, strongly shapes the policy to act decisively to resolve tasks within 45 seconds, and provides full transparency through real-time terminal output.
- **Touches:** `src/training/hospital_env.py`, `src/training/train_solo_1000ep.py`, `tests/test_stagnation_env.py`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** 3/3 tests in `tests/test_stagnation_env.py` pass; all 16 repo pytest tests pass; verified 10-episode GPU smoke run and initiated 1000-episode training on RTX 4060.


### D-030 — Expand Solo Patient PPO Training Target to 5000 Episodes
- **Status:** accepted
- **When:** 2026-10-24T15:07:00+07:00
- **Decided by:** human
- **Trigger:** "increase tje ep to 5000"
- **Decision:**
  1. The initial 1000-episode milestone concluded successfully at 1000 episodes (Peak $R_{team} = +234.0$, 1,036 patients helped, 28 full shifts completed).
  2. Stabilized advantage normalization in `src/training/train_solo_1000ep.py` using whole-batch `t_adv.std(unbiased=False)` and mini-batch size guards to eliminate single-element sample variance NaN hazards.
  3. Extended training target from 1000 to 5000 episodes (`--episodes 5000`), seamlessly resuming from checkpoint `PPOHospital-solo-1000ep_last.pt` at Episode 1001.
  4. Dynamically scaled `CosineAnnealingLR` over the remaining 4,000 episodes ($1.0 \times 10^{-4} \to 3.0 \times 10^{-5}$) with periodic checkpoint saving every 100 episodes.
- **Why:** Deepens policy convergence, solidifies complex multi-doorway escorting trajectories, and pushes the policy toward mastering back-to-back patient navigation with near-zero stagnation.
- **Touches:** `src/training/train_solo_1000ep.py`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** Clean resume from Episode 1001 running live under background task `task-3198` on RTX 4060 GPU with verified real-time logging and zero warnings.

### D-031 — Hospital Floor 2 Expansion, Two-Way Interactive Elevator, and Multi-Floor RL Navigation
- **Status:** accepted
- **When:** 2026-10-25T21:40:00+07:00
- **Decided by:** human-approved via `/grill-me` alignment (`floor2_elevator_plan.md`)
- **Trigger:** "we lack the rooms for floor two, create it, make it a seperate parts, not directly on top of the floor 1, elevator should works a sa teleport to floor 2 both up and down should have animation of going up and down"
- **Decision:**
  1. **Side-by-Side Floor 2 Architecture ($X = +50.0\,\text{m}$):** Created `sim_vision/godot/scenes/room_floor2.tscn` ($24\,\text{m} \times 18\,\text{m}$) containing Rooms 201/204 (Imaging/CT/X-ray), 205 (Gastroenterology), 210 (ENT), 220 (Dermatology), Floor 2 Waiting Lobby (`sanh_t2`), Restrooms (`wc_t2`), and Elevator Station 2. Placed side-by-side at $X = +50.0\,\text{m}$ inside `room.tscn` (not stacked vertically) to avoid ceiling culling conflicts and allow seamless camera panning without reloading scenes.
  2. **Interactive Elevator Station (`elevator_station.tscn`):** Created full 3D cabin station with dual sliding steel doors (`DoorLeft`, `DoorRight`), dynamic 3D LED floor displays ("TẦNG 1 ▲ / TẦNG 2 ▼"), high-fidelity two-tone Ding-Dong chime (`elevator_chime.wav`), and low-frequency motor hum (`elevator_hum.wav`).
  3. **Two-Stage Multi-Floor Routing & Animation:** In `rl_env_bridge.gd` and `main.gd`, escorting requests across floors (Floor 1 $\leftrightarrow$ Floor 2) dynamically guide to the departure floor elevator entrance $\to$ trigger full animated elevator sequence (doors slide open $\to$ passenger boarding $\to$ doors close $\to$ hum audio & LED arrow update $\to$ coordinate teleportation $\to$ destination chime $\to$ doors slide open $\to$ passenger exit $\to$ doors close) $\to$ update navigation goal to the final clinic on the arrival floor.
  4. **Multi-Floor RL Training Environment:** In `src/training/hospital_env.py`, generated `FLOOR2_WALLS` offset at $+50.0\,\text{m}$, enabled cross-floor elevator transit simulation with `REWARD_ELEVATOR_TRANSIT = +10.0`, and updated corridor doorway routing so PPO learns both local hallway navigation and cross-floor elevator boarding.
- **Why:** Solves the core bottleneck where 1-floor-trained models got stuck hitting the east wall when trying to navigate to Floor 2, adds realistic medical transport aesthetics, and keeps 3D physics fully decoupled across floors.
- **Touches:** `sim_vision/godot/scenes/room.tscn`, `sim_vision/godot/scenes/room_floor2.tscn`, `sim_vision/godot/scenes/props/elevator_station.tscn`, `sim_vision/godot/scripts/elevator_station.gd`, `sim_vision/godot/scripts/room.gd`, `sim_vision/godot/scripts/rl_env_bridge.gd`, `sim_vision/godot/scripts/main.gd`, `src/training/hospital_env.py`, `tests/test_floor2_elevator.py`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** 151/151 Godot GUT tests pass; 12/12 pytest unit tests pass (including multi-floor elevator transit test); verified GPU smoke training with warm-start weights from the 100k episode checkpoint.



### D-032 — Fix Patient Escort Geometric Deadlock and Velocity Mismatch During Inference
- **Status:** accepted
- **When:** 2026-10-26T16:25:00+07:00
- **Decided by:** human
- **Trigger:** "our newest training, but from what i saw when inference, the robot are literealy not works for escort patient, you test its our, by examining a specific case where patient ask for destination and see why the robot wont works experiments\runs\20261025_1248_PPOHospital"
- **Diagnosis:**
  1. **Geometric Arrival Deadlock (`GOAL_ARRIVE_PATIENT_M = 2.0m`):** In `main.gd` and `hospital_env.py`, goal arrival required both $d(\text{robot}, \text{goal}) \le 1.4\text{m}$ and $d(\text{patient}, \text{goal}) \le 2.0\text{m}$. However, `step_escorted_patient` halts the patient as soon as $d(\text{patient}, \text{robot}) \le 0.9\text{m}$. When the robot stopped at $1.2\text{m}$ from the goal, the trailing patient stopped at $1.2 + 0.85 = 2.05\text{m} > 2.0\text{m}$. Neither agent moved again, deadlocking task completion.
  2. **Escort Velocity Mismatch:** In `rl_policy_server.py`, robot speed uncapped reached $V_{\text{MAX}} = 0.80\,\text{m/s}$, while elderly patient walking speed is $0.48\,\text{m/s}$. Within 3 seconds, tether stretched past $2.2\,\text{m}$, triggering sharp policy speed collapse ($0.80 \to 0.21 \to 0.03\,\text{m/s}$) and severe right-turn steering bias ($\omega = -0.92\,\text{rad/s}$).
- **Decision:**
  1. Relaxed `GOAL_ARRIVE_PATIENT_M` from $2.0\,\text{m}$ to $2.5\,\text{m}$ in `src/training/hospital_env.py` and `sim_vision/godot/scripts/rl_env_bridge.gd`, safely accommodating $1.4\,\text{m} (\text{robot}) + 0.9\,\text{m} (\text{tether}) = 2.3\,\text{m} \le 2.5\,\text{m}$.
  2. In `sim_vision/python/rl_policy_server.py` and `src/training/hospital_env.py`, capped robot forward velocity during `TaskPhase.GUIDE_ESCORT` to `ESCORT_WALK_SPEED = 0.52 m/s` (matching patient walking speed of $0.48\,\text{m/s}$), preventing tether stretch and keeping $d_{\text{tether}}$ within the optimal $1.0 - 1.6\,\text{m}$ window.
- **Why:** Completely eliminates arrival deadlocks at destination clinics and elevators, avoids tether-stretch policy speed collapse, and raises multi-seed test success rate from 76.7% to 100.0%.
- **Touches:** `src/training/hospital_env.py`, `sim_vision/godot/scripts/rl_env_bridge.gd`, `sim_vision/python/rl_policy_server.py`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** 30-seed deterministic benchmark verified: success rate improved from 76.7% to 100.0% (0 failures); average patients helped increased from 1.27 to 1.70 (+34%); all 18 pytest tests pass.

### D-033 — Natural Patient Navigation, Animation Stabilization (T-Pose Option), and Multi-NPC Dialogue Targeting
- **Status:** accepted
- **When:** 2026-10-26T23:45:00+07:00
- **Decided by:** human
- **Trigger:** "the robot only target the red shirt patient, finetune it so it can adopt all the new patient", "and human animation seem flicking, why? if its too complicated, use t pose for now", "dont teleport the red shirt patient to the nearby possition of the robot anymore, make him a normal patient like other"
- **Decision:**
  1. **Disable Artificial Red-Shirt Teleportation:** In `sim_vision/godot/scripts/main.gd`, removed `is_task_transition` forced teleportation of the red-shirt patient. Placed the red-shirt patient at natural corridor coordinates `(4.5, 0.0, -1.35)` with waypoint loop and pardon behavior enabled, treating him as a standard patient alongside the other 6 seated/walking NPCs.
  2. **Multi-NPC Dynamic Dialogue Targeting:** In `main.gd`, replaced hardcoded references to `human` in `human_distance()` and `human_angle_deg()`. During dialogue states (`LISTEN`, `THINK`, `RESPOND`), distance and angle are evaluated against the active speaking patient (`get_active_speaking_patient()`), preventing incorrect angle/distance telemetry when other patients speak.
  3. **Animation Stabilization (`use_t_pose`):** Added `@export var use_t_pose: bool = false` in `human.gd` and enabled it in `main.tscn` to eliminate skeletal bone interpolation flickering/jitter while retaining the physics capsule collision shape and standard unit test compatibility.
- **Why:** Removes artificial biases toward the red-shirt patient, stabilizes visual animation rendering, and ensures the robot properly engages and escorts whichever patient initiates dialogue.
- **Touches:** `sim_vision/godot/scripts/human.gd`, `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/scenes/main.tscn`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** Verified all 7 human unit tests pass; red-shirt patient patrols corridor naturally; active speaking patient correctly becomes the focus of dialogue and escorting.

### D-034 — Dynamic 3D Door Labels and Hospital Department Signage Overhaul
- **Status:** accepted
- **When:** 2026-10-27T10:15:00+07:00
- **Decided by:** human-approved via `/grill-me` alignment (`plan_ui_door_signs_floor3.md`)
- **Trigger:** "all the rooms that can be destination for patient, must be writen in its name, because as I see right now, all of them have the tabs name in the door to be 'Phòng khám'"
- **Decision:**
  1. **Dynamic Door Label Tooling:** In `sim_vision/godot/scripts/sliding_door.gd`, added `@tool` annotation, exported property `door_label: String` with setter `set(val)`, and implemented `_update_labels()` to synchronize both front (`SignLabel3D`) and back (`SignBackLabel3D`) 3D labels directly in the Godot Editor viewport and at runtime.
  2. **Department Designation Overhaul:** Replaced generic "Phòng khám" labels across all floors with specific room numbers and hospital department titles:
     - **Floor 1:** `Door_101` ("101 - Phòng Cấp cứu"), `Door_110` ("110 - Phòng Khám Nội"), `Door_112` ("112 - Phòng Khám Ngoại"), `Door_Pharmacy` ("105 - Nhà thuốc Bệnh viện"), `Door_Lobby` ("100 - Quầy Tiếp đón & BHYT").
     - **Floor 2:** `Door_201` ("201 - Khoa Mắt"), `Door_204` ("204 - Khoa Răng Hàm Mặt"), `Door_205` ("205 - Khoa Tiêu hóa"), `Door_210` ("210 - Khoa Tai Mũi Họng"), `Door_220` ("220 - Khoa Da liễu").
     - **Floor 3:** `Door_301` ("301 - Khoa Tim mạch"), `Door_302` ("302 - Phòng Siêu âm tim"), `Door_303` ("303 - Phòng Điện tim ECG"), `Door_315` ("315 - Khoa Cơ xương khớp").
- **Why:** Eliminates clinical room ambiguity for human inspection and robot navigation, matching the NLU slot destinations in hospital dialogue.
- **Touches:** `sim_vision/godot/scripts/sliding_door.gd`, `sim_vision/godot/scenes/room.tscn`, `sim_vision/godot/scenes/room_floor2.tscn`, `sim_vision/godot/scenes/room_floor3.tscn`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** Verified in Godot Editor and runtime; door labels show clear room numbers and specialty titles on both sides; sliding door unit tests pass.

### D-035 — Floor 3 Hospital Extension and Multi-Floor Dynamic Elevator Navigation (X = +100.0m)
- **Status:** accepted
- **When:** 2026-10-27T11:20:00+07:00
- **Decided by:** human-approved via `/grill-me` alignment (`plan_ui_door_signs_floor3.md`)
- **Trigger:** "plan for adding floor number 3, which include all the destinated one for that floor"
- **Decision:**
  1. **Side-by-Side Floor 3 Modular Scene ($X = +100.0\,\text{m}$):** Created `sim_vision/godot/scenes/room_floor3.tscn` ($24\,\text{m} \times 18\,\text{m}$) containing Rooms 301 (Cardiology), 302 (Echocardiography), 303 (Electrocardiogram ECG), 315 (Orthopedics), Floor 3 Waiting Lobby (`sanh_t3`), Restrooms (`wc_t3`), and `Floor3Elevator` (`current_floor = 3`). Instantiated at $X = +100.0\,\text{m}$ inside `room.tscn`.
  2. **Generalized Multi-Floor Elevator Transit Formula:** In `sim_vision/godot/scripts/main.gd`, generalized elevator translation:
     $$\Delta X = (to\_floor - from\_floor) \times 50.0\,\text{m}$$
     Supporting any combination of Floor 1 ($0\,\text{m}$), Floor 2 ($50\,\text{m}$), and Floor 3 ($100\,\text{m}$) travel.
  3. **Dynamic Camera & Occlusion Handling:** Clamped camera orbit center dynamically ($X_{\text{center}} = 100\,\text{m}$ for $X \ge 75\,\text{m}$, $50\,\text{m}$ for $25 \le X < 75\,\text{m}$, and $0\,\text{m}$ for $X < 25\,\text{m}$) and cached Floor 3 interior walls for see-through transparency.
  4. **Multi-Floor RL Environment Routing:** Updated `Room.get_floor()`, `Room.get_room_floor()`, `rl_env_bridge.gd`, and `src/training/hospital_env.py` to route Floor 3 clinical keys (`301`, `302`, `303`, `315`, `dept_tim_mach`, `dept_co_xuong_khop`, `sanh_t3`) through the nearest elevator station and to destination clinic doors.
- **Why:** Fully supports Floor 3 departments referenced in clinical dialogue, expands hospital capacity to 3 complete floors, and keeps multi-floor physics decoupled and modular.
- **Touches:** `sim_vision/godot/scenes/room_floor3.tscn`, `sim_vision/godot/scenes/room.tscn`, `sim_vision/godot/scripts/room.gd`, `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/scripts/rl_env_bridge.gd`, `src/training/hospital_env.py`, `sim_vision/godot/tests/test_room.gd`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** 18/18 GUT tests in `test_room.gd` pass (16,516 asserts); 6/6 GUT tests in `test_rl_env.gd` pass; 35/35 Python pytest tests pass.

### D-036 — Robot Inspection Telemetry HUD Panel with 4-Tabbed Progress Bar Visualizations
- **Status:** accepted
- **When:** 2026-10-27T14:40:00+07:00
- **Decided by:** human-approved via `/grill-me` alignment (`plan_ui_door_signs_floor3.md`)
- **Trigger:** "update the UI in the top left conner when in the robot inspection cameras, it have a open/closable tab in that, if open it display the values of every inputs data sperate in tabs like you describe using process bar"
- **Decision:**
  1. **Component Design (`InspectionPanel`):** Created `sim_vision/godot/scripts/inspection_panel.gd` and `sim_vision/godot/scenes/inspection_panel.tscn` anchored at top-left (`UI/InspectionPanel` in `main.tscn`).
  2. **Collapsible Header & Shortcut Controls:** Added a toggle button `[▼] TELEMETRY / [▲] CLOSE` with status summary chips, supporting mouse click toggling and keyboard hotkeys (`I` / `Tab`).
  3. **4 Data Tabs with Real-Time Progress Bars and Numeric Labels:**
     - **Tab 1: LiDAR (17 Rays, 200° Fan):** 17 progress bars ($0.0 - 6.0\,\text{m}$) color-coded green ($\ge 1.5\,\text{m}$), yellow ($0.8 - 1.5\,\text{m}$), and red ($< 0.8\,\text{m}$).
     - **Tab 2: YOLO Vision:** Patient detection confidence bar ($0-100\%$), normalized centroid offset $C_x$ with left/right bias indicator, and bounding box height $H$ ($0.0 - 1.0$) with arrival threshold marking at $0.35$.
     - **Tab 3: RL Navigation:** Active task phase badge (`SEARCH_PATIENT`, `APPROACH_PATIENT`, `GUIDE_ESCORT`, `CALL_STAFF`), geodesic goal distance ($0 - 20\,\text{m}$), heading angle indicators ($\sin\theta, \cos\theta$), patient escort tether distance ($1.6\,\text{m}$ ideal, $2.5\,\text{m}$ max limit), linear velocity $V$, and angular velocity $\omega$.
     - **Tab 4: Voice & NLU:** STT & TTS connection chips, ASR transcribed hypothesis text, NLU intent & extracted slot, and target floor & clinic destination.
  4. **Performance Optimization:** Telemetry bars and text fields update only when the panel is expanded (`is_open == true`), incurring zero rendering overhead when collapsed.
- **Why:** Provides human operators and researchers with full, transparent visibility into the robot's real-time sensory and decision-making state during inspection camera view without cluttering the main 3D viewport.
- **Touches:** `sim_vision/godot/scripts/inspection_panel.gd`, `sim_vision/godot/scenes/inspection_panel.tscn`, `sim_vision/godot/scenes/main.tscn`, `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/tests/test_inspection_panel.gd`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** 4/4 GUT tests in `test_inspection_panel.gd` pass; all 163 GUT suite tests pass across the repository (18,873 asserts); hotkeys `I` and `Tab` toggle the panel cleanly.

### D-037 — Dedicated 3-Floor Patient Escort PPO Training & Distraction Guard
- **Status:** accepted
- **When:** 2026-10-27T18:30:00+07:00
- **Decided by:** human-approved via `/grill-me` alignment (`train_3floor_escort_2000ep_plan.md`)
- **Trigger:** "draft up a training plan, focus solly on escort patient on both 3 floors, train for 2k episode first /grill-me/grill-me", "to prevent deadlock (aka talk and accept too many escort, make the robot so that it will not be distract by other people until the current task is complete)"
- **Decision:**
  1. **Distraction Guard (Anti-Deadlock Mechanism):**
     - In `sim_vision/godot/scripts/main.gd`, added `is_task_busy() -> bool` returning `true` when `active_escorted_patient != null` or when the robot is actively executing an escort/call-staff task phase.
     - In `dialogue_manager.gd`, guarded `_on_talk_started()` and `register_npc()`: incoming NPC speech triggers and interaction popups are dropped/ignored whenever `main.is_task_busy()` is true, preventing dialogue interruption or task overwriting while an escort is underway.
  2. **Multi-Floor Environment & Dynamic Stagnation Reset:**
     - Updated `src/training/hospital_env.py` and `rl_controller.gd` with Floor 3 obstacles (31 rects, total 155 rects across 3 floors), north/south door routing, and elevator positions.
     - Enforced `escort_only=True` mode: 100% escort focus, balanced with 50% cross-floor elevator journeys ($F_1 \leftrightarrow F_2, F_1 \leftrightarrow F_3, F_2 \leftrightarrow F_3$) and 50% same-floor clinic escort.
     - Dynamic Stagnation Reset: 60s base timeout, with clock reset to 0 whenever an elevator transit occurs or the robot advances $\ge 1.0\,\text{m}$ toward its active goal.
  3. **Dedicated Trainer Script (`train_3floor_escort_2000ep.py`):**
     - Warm-started from full-patient policy (`20261026_214227_PPOHospital-full-patient`).
     - 2000 episodes on NVIDIA RTX 4060 GPU with Cosine Annealing LR ($1.0 \times 10^{-4} \to 3.0 \times 10^{-5}$), teacher prior decaying $0.05 \to 0.0$ over first 300 episodes, and deterministic evaluation every 200 episodes on 20 held-out seeds.
- **Why:** Eliminates deadlock caused by bystander NPC interruptions during patient transport, equips the PPO policy with multi-floor elevator transit navigation, and focuses learning entirely on patient escort delivery.
- **Touches:** `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/scripts/dialogue_manager.gd`, `sim_vision/godot/scripts/rl_controller.gd`, `src/training/hospital_env.py`, `src/training/hospital_layout.json`, `src/training/train_3floor_escort_2000ep.py`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** Full 2000-episode training run completed in 2h43m (9,839.7s) on NVIDIA RTX 4060 GPU (`experiments/runs/20261027_183421_PPOHospital-3floor-escort-2k`):
  - **Completed Shifts:** 2,000 / 2,000 (100% completion rate).
  - **Patients Escorted:** 7,362 (average 3.68 patients helped per 240s shift).
  - **Stagnation Timeouts:** 0 (0.0% stagnation rate across all 2,000 episodes and all evaluation checkpoints).
  - **Best Rolling-20 $R_{team}$:** +158.10 (Peak $R_{team}$: +246.00).
  - **Best Deterministic Eval Score:** +134.00 (3.30 tasks/shift, 0.0 collisions across 20 held-out seeds).
  - **Checkpoints Saved:** `PPOHospital-3floor-escort_best.pt` and `PPOHospital-3floor-escort_last.pt`.

### D-038 — Escort-Only Inference Mode, Overlay HUD Escort Label, and Manual Test Hotkey
- **Status:** accepted
- **When:** 2026-10-27T19:00:00+07:00
- **Decided by:** human
- **Trigger:** "hey, i see the inference the escort doest works at all, the robot just sat there, and the status got updated to arrived, no where to see the escort, make a modifle or flag for the inference/test code for patient to only ask for escort for me to check more throughtly"
- **Decision:**
  1. **Root Cause Identification:**
     - In speech dataset `sim_vision/godot/assets/voices/clips.json`, most clips map to non-escort intents (`dang_ky_kham`, `bao_hiem`, etc.), which trigger verbal answer and patient reset rather than an escort task.
     - In `main.gd`, `_step_policy()` passed `current_target_patient` rather than `active_escorted_patient`, triggering an artificial 10m tether break and stopping the robot during escort.
     - Overlay HUD displayed `Config.state_name(state)` which froze on `"ARRIVED"` even while actively navigating.
     - `_physics_process()` lacked `"thang_may_t3"` in elevator transition triggers.
  2. **`--escort-only` Simulation Flag:**
     - In `npc.gd`, added `const ESCORT_INTENTS = ["hoi_phong", "hoi_khoa", "dan_duong"]` and `escort_only` property to filter voice clips strictly to clinical destination escort requests.
     - In `run_simulation.py`, added `--escort-only` CLI argument forwarded to Godot.
     - In `main.gd`, parsed `--escort-only` and applied it to all hospital NPCs; if a non-escort intent somehow completes, promoted it to a multi-floor clinic escort.
  3. **Inference Navigation & HUD Overhaul:**
     - Fixed `_step_policy()` to measure distance and tether relative to `active_escorted_patient`.
     - Added `_display_state_name()` displaying `"ESCORT: <dest>"` or `"CALL_STAFF"` in the HUD overlay.
     - Added `thang_may_t3` to elevator transition checks.
     - Added `KEY_G` hotkey in `main.gd` calling `trigger_test_escort()` to instantly dispatch an escort task to Floors 1, 2, or 3 for immediate interactive testing.
  4. **Dedicated CLI Policy Test Script:**
     - Created `src/training/test_3floor_escort.py` to run headless multi-episode evaluations of trained escort checkpoints with step-by-step logs of elevator rides, patient pacing, and arrivals.
- **Why:** Guarantees 100% escort task testing without waiting through non-escort Q&A dialogues, corrects policy tether tracking in Godot 3D, and provides clear visual feedback of the active escort destination.
- **Touches:** `run_simulation.py`, `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/scripts/npc.gd`, `src/training/test_3floor_escort.py`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** `pytest` test suite passes (26/26 passed); `python -m src.training.test_3floor_escort --episodes 2` completes with 6/6 patients escorted and 5 elevator transits; verified in Godot runtime with `--escort-only` and `G` key.

### D-039 — Fix Solo Patient Targeting, Busy Guard, and Dialogue-to-Escort Transition
- **Status:** accepted
- **When:** 2026-10-30T07:00:00+07:00
- **Decided by:** human-approved via `/grill-me` alignment
- **Trigger:** "in the godot 3d simulation: the robot drive up to the patient? it movment is weird, the patient do speak, but no escort start, it sit there, after like 3-5s, it tries to find other patient"
- **Decision:**
  1. **Fix Solo-Patient Target Selection:**
     - In `sim_vision/godot/scripts/main.gd:get_available_patients()`, fixed logic so in `solo_patient_mode` it strictly returns `[human]` (`$Human`), preventing the robot from pursuing invisible or disabled furniture NPCs on other floors.
     - Updated `_nearest_person_distance()` in `main.gd` to ignore furniture NPCs during solo mode.
     - In `reset_positions(is_task_transition)`, kept the robot in place and re-positioned the solo `$Human` at a reachable corridor/lobby spot on the current floor ($\ge 3\,\text{m}$ away) instead of teleporting the robot back to spawn.
  2. **Refine Busy Guard (`APPROACH_PATIENT` Removal):**
     - In `main.gd:is_task_busy()`, removed `APPROACH_PATIENT` from busy states. This ensures that while the robot is driving toward a target patient, NPCs can evaluate the robot as receptive and trigger `_start_talk()` once the robot arrives.
  3. **Seamless Dialogue-to-Escort Transition:**
     - In `main.gd:_on_dialogue_turn_completed()`, prevented state overwriting during dialogue so `state == RESPOND` stays intact until audio and subtitles complete.
     - In `main.gd:set_dialogue_state()`, when returning to `ARRIVED` upon completion of dialogue speech, if `is_task_busy()` is true (an escort was scheduled), immediately transitions to `Config.RobotState.APPROACH` so the robot and patient begin walking without a 3-5s stall or abort reset.
     - In `sim_vision/godot/scripts/dialogue_manager.gd:_after_response()`, fixed the speaker reference to use `target_npc = active_npc if active_npc != null else npc`.
  4. **Escort Clip Filtering & Unit Test Conformance:**
     - In `sim_vision/godot/scripts/npc.gd`, excluded clip sentence `05` (symptom advice query lacking destination slot) in `escort_only` mode.
     - Fixed `pick_clip()` fallback to strictly adhere to GUT test specification by returning `""` on empty speaker clips.
- **Why:** Solves the root causes of the simulation stall where the robot reached the patient but failed to begin escorting, eliminated erratic navigation toward furniture NPCs, and ensures instantaneous start of patient walking upon speech completion.
- **Touches:** `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/scripts/dialogue_manager.gd`, `sim_vision/godot/scripts/npc.gd`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** All GUT unit tests pass cleanly (163/163 passed, 18,873 asserts); all Python pytest tests pass (26/26 passed); verified smooth immediate transition from voice completion to walking in solo-patient escort mode.

### D-040 — Fix GDScript STT/TTS Connection Property Crash in Dialogue Turn Completed
- **Status:** accepted
- **When:** 2026-10-30T07:40:00+07:00
- **Decided by:** human-directed log analysis
- **Trigger:** "SCRIPT ERROR: Invalid access to property or key 'connected' on a base object of type 'Node (SttClient)'. at: Main._on_dialogue_turn_completed (res://scripts/main.gd:438)"
- **Decision:**
  1. **Root Cause Analysis:**
     - During normal dialogue execution, when `dialogue.turn_completed` signal fired, `_on_dialogue_turn_completed` in `sim_vision/godot/scripts/main.gd` attempted to access `dialogue.stt.connected` and `dialogue.tts.connected` to update the HUD telemetry inspection panel.
     - `SttClient` and `TtsClient` encapsulate their connection status behind the public method `is_server_connected() -> bool` (`_connected` is private).
     - Accessing `.connected` raised an uncaught GDScript runtime exception that aborted `_on_dialogue_turn_completed` before reaching line 446. Consequently:
       - `active_escorted_patient` was never assigned.
       - `_rl_bridge.begin_post_dialogue_task(...)` was never called.
       - The task phase remained stuck at `SEARCH_PATIENT`, leaving the robot stationary until the 10s non-response timer timed out and reset the interaction.
     - In contrast, pressing `KEY_G` bypassed `_on_dialogue_turn_completed` and directly invoked `_rl_bridge.begin_post_dialogue_task()`, which explained why `G` escorted reliably while normal dialogue failed.
  2. **Code Resolution:**
     - In `sim_vision/godot/scripts/main.gd:439-440`, updated property access to method call:
       ```gdscript
       dialogue != null and dialogue.stt != null and dialogue.stt.is_server_connected(),
       dialogue != null and dialogue.tts != null and dialogue.tts.is_server_connected(),
       ```
- **Why:** Restores normal speech-driven dialogue turn completion and eliminates the script exception, allowing the escort state transition and RL policy dispatch to execute seamlessly when patients finish speaking.
- **Touches:** `sim_vision/godot/scripts/main.gd`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** All 163 GUT unit tests pass without error (18,873 asserts, 140.9s); confirmed no other invalid `.connected` accesses remain across the codebase.

### D-041 — Fix Escort Patient Trapping Behind Furniture and Dynamic Trail Pruning
- **Status:** accepted
- **When:** 2026-10-30T07:55:00+07:00
- **Decided by:** human log observation
- **Trigger:** "the patient not follow the bot, why? ... Robot=(-0.65, 3.94) Patient=(-2.72, 6.36) tether=3.19m"
- **Decision:**
  1. **Root Cause Analysis from Telemetry:**
     - The telemetry logs showed the patient moved from `(-3.24, 6.36)` to `(-2.72, 6.36)` and then completely froze while the robot moved towards the elevator.
     - Hospital layout inspection revealed `Furniture/WaitingBenchWestBack/Collision` sits at $X \in [-4.875, -2.725], Z \in [5.49, 6.11]$. The patient at $X = -2.72, Z = 6.36$ was physically pressing against the back of the waiting bench.
     - Why were they separated? `pick_solo_start_positions()` in `main.gd` had sampled `human_pos` using `get_free_position()` into the bench nook, then randomly spawned the robot across the bench in the front lobby ($Z \le 5.32$) without checking for line-of-sight obstruction. The robot approached to engage distance ($1.35\,\text{m}$) across the bench, spoke with the patient, and began escorting. The straight path from patient to robot's first crumb collided with the bench.
     - Furthermore, `step_escorted_patient()` in `rl_env_bridge.gd` strictly popped `trail[0]` only when distance was $\le 0.3\,\text{m}$ (`ESCORT_CRUMB_REACH_M`). Because the trapped patient stayed at $1.22\,\text{m}$ from the initial crumb, `trail.pop_front()` was never called; the patient remained permanently fixated on the blocked initial crumb rather than following the robot forward.
  2. **Code Resolution:**
     - **Lobby Patient Spawn Bounds (`room.gd`):** Trimmed `PATIENT_LOBBY_RECT` to `Rect2(Vector2(-3.2, 2.2), Vector2(6.4, 2.8))` ($Z \in [2.2, 5.0]$), matching Python training `HospitalShiftEnv._sample_patient_spawn_solo()` exactly and preventing patient spawns behind lobby benches.
     - **Solo Start Placement with Obstacle-Free LOS (`main.gd`):** Updated `pick_solo_start_positions()` to sample `human_pos` from `r.get_patient_spawn_position(1, rng)` and verify an unobstructed line of sight to candidate `robot_pos` using `AABB.intersects_segment()`.
     - **Fresh Trail Initialization (`rl_env_bridge.gd`):** In `begin_post_dialogue_task()`, cleared `escort_trail` and initialized with current robot position so past crumbs never linger.
     - **Adaptive Trail Progression (`rl_env_bridge.gd`):** Updated `step_escorted_patient()` while-loop to advance if `d0 <= ESCORT_CRUMB_REACH_M or d1 <= d0`. If the patient is already closer to the next waypoint `trail[1]`, obsolete crumbs are pruned automatically, preventing backtracking and deadlock.
- **Why:** Ensures the patient spawns in open walkable areas with clear access to the robot, and allows breadcrumb following to smoothly progress along the robot's trail without getting stuck on past crumbs.
- **Touches:** `sim_vision/godot/scripts/room.gd`, `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/scripts/rl_env_bridge.gd`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** 163/163 GUT unit tests pass (18,873 asserts, 140.3s). Patient now has direct, open access to follow robot along the breadcrumbs.

### D-042 — Seated Patient Interaction Position, Stand-Up Transition, and Physics Collision Fix
- **Status:** accepted
- **When:** 2026-10-30T08:15:00+07:00
- **Decided by:** AI-pair (Manh + Antigravity)
- **Trigger:** "ok, this time I run without solo patient, and the robot pick up a random patient, but its did not follow ... Robot=(-0.99, 3.44) Patient=(-3.59, 3.50) tether=2.60m"
- **Decision:**
  1. **Root Cause Analysis from Telemetry:**
     - In full hospital simulation (with crowd NPCs), the robot selected `Patient_01` who was seated on `WaitingBenchWest` at $X = -4.55, Z = 4.20$.
     - `main.gd` previously passed raw `target_p.global_position` ($Z = 4.20$) to the RL policy and distance metrics. During Python training (`hospital_env.py:761`), seated targets were explicitly placed at `cand_z = chosen["z"] - 0.9` ($Z = 3.3$, in the open corridor aisle). In Godot, raw bench coordinates caused the robot to approach from the north passage behind the bench and stop at `Robot=(-3.47, 4.99)`.
     - Dialogue triggered across the backrest of the bench. When escort started, the robot moved towards the elevator, dropping its initial crumb behind the bench. `Patient_01` stood up at $Z = 3.50$ and attempted to move north towards the crumb, physically colliding with `WaitingBenchWest` ($Z \in [3.89, 4.51]$).
     - Furthermore, in `hospital_npc.gd:226-230`, `global_position += disp` ran unconditionally without an `else` branch after `move_and_slide()`, forcing the character capsule directly into the static bench collision geometry every frame and inducing physics lockup.
  2. **Code Resolution:**
     - **Interaction Position (`hospital_npc.gd`):** Added `get_interaction_position() -> Vector3`. If `is_seated`, returns `waypoints[1]` (which is explicitly placed in the open corridor aisle at $Z = 2.50$) or an offset $0.9\,\text{m}$ in front of the seat, matching training assumptions.
     - **Stand-Up Transition (`hospital_npc.gd`):** In `set_state(State.ESCORTED)` and `escort_step_towards()`, if `is_seated`, automatically clears seated state and places the NPC at their open aisle waypoint (`waypoints[1]`) before movement begins.
     - **Physics Collision Preservation (`hospital_npc.gd`):** Fixed `escort_step_towards()` and `_move_step_towards()` to place `global_position += disp` inside an `else:` branch, allowing Godot's `move_and_slide()` to resolve collisions naturally without forced penetration.
     - **Dialogue & Policy Alignment (`main.gd` & `npc.gd`):** Updated `_step_policy()`, `human_distance()`, `human_angle_deg()`, and `npc.gd:_process()` to use `get_interaction_position()`, ensuring the robot approaches the patient from the open corridor in front of the bench.
     - **Crumb Clearance (`rl_env_bridge.gd`):** Updated `ESCORT_CRUMB_REACH_M = 0.45` to permit smooth capsule navigation around lobby furniture.
- **Why:** Ensures seated patients are approached from the open aisle rather than from behind furniture, cleanly stand up into walkable space when escort begins, and smoothly follow the breadcrumb trail without physics collisions.
- **Touches:** `sim_vision/godot/scripts/hospital_npc.gd`, `sim_vision/godot/scripts/main.gd`, `sim_vision/godot/scripts/npc.gd`, `sim_vision/godot/scripts/rl_env_bridge.gd`, `docs/AI-Human-logs/Vuong.md`
- **Evidence:** GUT unit tests passing; verified patient stands up in the corridor and follows breadcrumbs without colliding into bench geometry.

### D-043 — Analysis of Duty Cycle Flaws, Oracle Dispatch vs Visual RL, and Pure Visual-Search RL Roadmap
- **Status:** accepted
- **When:** 2026-10-30T08:50:00+07:00
- **Decided by:** human-directed architectural review
- **Trigger:** Human identified two fundamental operational and training flaws: 1) Patient repeated request after arriving at clinic room; 2) Robot stranded on upper floors without a return-to-lobby mechanism; 3) Revelation that current RL policy relies on oracle patient coordinates rather than visual search.
- **Decision:**
  1. **Root Cause Analysis — Patient Lifecycle & Duty Cycle:**
     - When arriving at destination (e.g. Room 205 on Floor 2), the escorted patient stayed standing outside the room without being flagged as completed (`helped = true`).
     - `main.gd:355` filtered next targets by current floor (`same_fl`). Since Floor 2/3 had no crowd patients, the single newly arrived patient was immediately re-targeted, triggering dialogue again.
     - In training (`hospital_env.py:756`), new patients were artificially spawned on the robot's current floor (`x_base = floor_of(robot)`), omitting the critical hospital duty cycle where the robot rides the elevator down to Floor 1 Lobby to collect new outpatients.
  2. **Architectural Contrast — Vision FSM vs Goal-Conditioned RL:**
     - FSM mode (`--controller fsm`) searches using YOLOv8 camera vision, scanning the room and steering via bounding box coordinates ($c_x, h$).
     - RL mode (`--controller rl`) operates as an Oracle-Dispatched Goal-Directed Agent: observation vector (31 dims) only takes 17 LiDAR rays and a goal vector $(d_{\text{goal}}, \Delta\theta)$ fed from simulation ground-truth coordinates. The camera/YOLO feed is only used for HUD overlay and CSV logging; the PPO network is blind to vision.
  3. **Strategic Direction (Pure RL Vision-Search Roadmap):**
     - Transition from oracle dispatch toward a Pure RL-driven robot that actively searches for patients using vision/detections without hardcoded or ground-truth patient coordinates.
     - Known static landmarks (rooms, elevator doors) may remain fixed map coordinates, but human target acquisition must be visual and learned.
- **Why:** Establishes complete parity between actual clinical hospital operations (Lobby $\to$ Escort $\to$ Clinic Room $\to$ Return to Lobby) and provides the architectural foundation for a true Visual Search RL agent.
- **Touches:** `docs/AI-Human-logs/Vuong.md`, `sim_vision/godot/scripts/main.gd`, `src/training/hospital_env.py`
- **Evidence:** Comprehensive codebase analysis confirming `_on_detections()` bypasses YOLO during RL mode; theoretical and empirical proof of duty cycle deadlock when multi-floor transition finishes.

### D-044 — /grill-me Interview Record: Pure Visual-Search RL Architecture and New Training Branch
- **Status:** accepted
- **When:** 2026-10-30T09:10:00+07:00
- **Decided by:** human-approved via /grill-me
- **Trigger:** Human requested a rigorous architectural interview (`/grill-me`) to design a Pure RL-driven robot that actively discovers patients through vision without oracle ground-truth coordinates, while preserving LiDAR obstacle avoidance and room escorting.
- **Decision:**
  1. **Q1 — Vision Observation Representation:**
     - *Question:* How should visual patient information be fed to the PPO policy?
     - *Decided:* **Feature-Level Vision Observation (YOLO Bounding Box Features + LiDAR + Nav Goals)**. Compact vector containing `[person_seen, norm_cx, norm_cy, box_w, box_h]` combined with 17 LiDAR rays and kinematic state. Enables ultra-fast PPO simulation (>5,000 steps/s in Python) and direct transfer to YOLOv8 inference in Godot.
  2. **Q2 — Motion during SEARCH (No Patient in FOV):**
     - *Question:* How should the robot move when searching and no patient is visible?
     - *Decided:* **Autonomous Exploration / Curiosity & Area Coverage Reward**. During SEARCH, the goal vector is neutral $(0, 0)$. The robot explores the hospital floor autonomously driven by intrinsic coverage incentives until a patient enters camera FOV. (Recommended patrol waypoints documented as fallback baseline).
  3. **Q3 — Multi-Floor Duty Cycle & Return-to-Lobby:**
     - *Question:* How does the robot learn to take the elevator down to Floor 1 after completing an escort on Floor 2/3?
     - *Decided:* **Implicit Opportunity Return (Sparse Penalty Formulation)**. No privileged multi-floor oracle state. Robot experiences a per-step time penalty (`-0.01/step`). Upper floors without waiting patients represent a reward desert; the robot must discover that riding the elevator down to Floor 1 unlocks high task completion rewards (+30.0).
  4. **Q4 — Visual Patient Acquisition Reward:**
     - *Question:* What reward guides the robot when a person is visible (`seen = 1`)?
     - *Decided:* **Visual Acquisition Reward**. Positive reward for detection (+2.0 when `seen=1`), camera centering penalty ($-|c_x|$ to align the robot's heading), and distance reduction shaping ($+h$ scaling up to $0.45$). Reaching $h \ge 0.45$ triggers engagement and dialogue.
  5. **Q5 — Fast Python Simulation of Vision:**
     - *Question:* How should the camera be modeled in fast Python simulation (`hospital_env.py`)?
     - *Decided:* **Geometric Pinhole Camera Model with Line-of-Sight and Domain Randomization**. $75^\circ$ FOV horizontal projection with $c_x = \tan\Delta\theta / \tan(\text{FOV}/2)$, $h \propto 1/D$, and raycast occlusion check. Domain randomization ($\pm 5\%$ jitter and frame dropout) ensures robustness against real-world YOLOv8 detection fluctuations during Godot inference.
  6. **Q6 — Implementation Roadmap:**
     - *Decided:* **Option 2: Focus 100% on the new Pure Visual RL environment on a dedicated Git branch (`feat/pure-visual-rl`)**, developing `hospital_env_vision.py` and `train_visual_rl.py`.
- **Why:** Replaces privileged oracle coordinates with genuine sensorimotor visual acquisition, uniting YOLO perception and PPO control into an authentic end-to-end autonomous robotic agent.
- **Touches:** `docs/AI-Human-logs/Vuong.md`, `src/training/hospital_env_vision.py`, `src/training/train_visual_rl.py`
- **Evidence:** Recorded interview consensus; architectural design verified against Pinhole optics, PPO sample complexity, and Godot 3D camera parameters.




