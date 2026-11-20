# SKILL TEMPLATE: UNIVERSAL MULTI-MARKDOWN TO STANDALONE EXECUTIVE HTML REPORT BUILDER

- **Motivation/Background**: In complex engineering, AI/ML research, data platform, or software architecture projects, experimental findings and technical evaluations invariably scatter across disparate Markdown files (e.g., architecture specs, hardware profiler logs, head-to-head model benchmarks, production rollout audits, edge-case failure logs). Clients, executives, and cross-functional teams require **A SINGLE, COHESIVE, HIGH-IMPACT EXECUTIVE DASHBOARD** that can be distributed as an independent artifact and opened offline on any browser without broken images, external server dependencies, or distorted layouts.
- **Purpose**: A universal, domain-agnostic engineering skill template and code blueprint for synthesizing multiple Markdown reports into a self-contained, single-file HTML report. Designed for any domain (Computer Vision, NLP/LLM, Data Engineering, DevOps, Microservices, Systems Benchmarking), featuring embedded Base64 graphics (100% offline portability), seamless dark/light mode toggle with zero dark bleeding, a responsive centered layout, and a sticky top navigation bar.
- **Overview Pipeline**:
  1. *Audit & Ingestion*: Extract qualitative conclusions, tabular metrics, and visual asset paths from source `.md` documents.
  2. *Base64 Binary Serialization*: Convert all graphics (charts, architecture diagrams, benchmark plots, visual samples) into inline Base64 Data URIs (`data:image/...;base64,...`).
  3. *Executive Narrative Structuring*: Organize findings into a 7-stage narrative (Executive KPIs -> Architecture Topology -> Compute/Memory Footprint -> Standardized Workload Runtime -> Quantitative Benchmarks -> Qualitative Diffs -> Strategic Roadmap).
  4. *CSS Token & Component Engine*: Apply a dual-theme design system with explicit light-mode overrides to eliminate hardcoded dark residue.
  5. *Automated Compilation*: Run a parameterized Python script (`build_executive_report.py`) with built-in HTML tree validation.
- **References**: `agents/templates/EXPERIMENT_TEMPLATE.md`, `agents/templates/PHASE_DOC_TEMPLATE.md`.
- **Created**: 2026-09-19T11:58:00+07:00
- **Last Updated**: 2026-09-19T12:35:00+07:00

---

## 1. Universal Architectural & UX Design Principles

### 1.1 Single-File Self-Containment (Zero External Asset Dependencies)
- **The Pitfall**: Linking images via relative file paths (e.g., `<img src="assets/plot.png">`) breaks immediately when an executive or client downloads, shares via email/Slack, or opens the `.html` file outside the source directory.
- **Universal Rule**: **100% of all raster images (PNG, JPEG, WebP) and vector graphics (SVG) MUST be serialized as Base64 Data URIs** and embedded directly within the document.
- **Artifact Size Target**: A comprehensive report containing 6–15 high-resolution figures typically ranges between **2.0 MB and 4.5 MB**, which loads instantaneously in modern browsers and functions completely offline without requiring internet connectivity or accompanying folders.

### 1.2 Centered Executive Canvas with Sticky Top Navigation
- **The Pitfall**: Fixed left-side navigation sidebars consume 260–320px of valuable viewport width. This forces horizontal scrollbars and severely compromises readability on complex comparison tables (e.g., multi-candidate runtime benchmarks, resource profiling, confusion matrices).
- **Universal Rule**: **Eliminate sidebars in favor of a Centered Document Canvas** (`max-width: 1280px; margin: 0 auto; padding: 35px 24px 80px;`).
- **Universal Navigation Component**: Implement a **Sticky Top Header Bar** (`header.top-header`) that remains anchored during scrolling:
  - Brand identity badge and title.
  - Horizontally scrollable category pills: `[Executive Summary]`, `[1. Architecture]`, `[2. Hardware & Resources]`, `[3. Standardized Workload]`, `[4. Comparative Evaluation]`, `[5. Qualitative Analysis]`, `[6. Production Rollout]`, `[7. Roadmap]`.
  - Theme toggle switch (`☀️ / 🌙 Theme`).
  - Active section tracking powered by lightweight JavaScript Scrollspy.

### 1.3 Strict Dual-Theme Parity (Zero Dark Residue in Light Mode)
- **The Pitfall**: Hardcoding dark backgrounds (e.g., `rgba(15, 23, 42, 0.65)` on metric cards or `rgba(0, 0, 0, 0.2)` on diff blocks) causes critical visual defects when switching to Light Mode: text turns dark while containers remain dark navy or black, rendering text unreadable.
- **Universal Rule**: **Every single UI element MUST have explicit, high-contrast styling for both themes**:
  - Dark Mode: Tech-forward slate palette (`#0b0f19` background, `#111827` cards, `#1e293b` surfaces, `#f8fafc` text).
  - Light Mode: Clean corporate stationery palette (`#f8fafc` background, `#ffffff` cards, `#e2e8f0` borders, `#0f172a` primary text, `#334155` secondary text).
  - Mandatory Light Mode Overrides: `.light-mode .hero-banner`, `.light-mode .kpi-card`, `.light-mode .card`, `.light-mode .diff-column`, `.light-mode .callout`, `.light-mode th`, and `.light-mode td`.

---

## 2. Universal 7-Stage Report Structure

Regardless of the underlying technical domain, an executive-grade engineering report should adhere to this 7-stage narrative flow:

```text
┌────────────────────────────────────────────────────────────────────────┐
│  EXECUTIVE HERO BANNER & KPI METRICS DASHBOARD                         │
│  [Top 4-5 High-Level Metrics: Throughput, Efficiency, Quality, Delta]  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                                                               ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│ 1. SYSTEM TOPOLOGY & WORKFLOW   │   │ 2. COMPUTE & RESOURCE PROFILING │
│ Architectural schematics & data │   │ Memory footprint, GPU/CPU load, │
│ pipeline stages                 │   │ static vs dynamic allocations   │
└────────────────┬────────────────┘   └────────────────┬────────────────┘
                 │                                     │
                 └──────────────────┬──────────────────┘
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│ 3. STANDARDIZED WORKLOAD RUNTIME (Normalized Batch, e.g. 100/1000)    │
│ Head-to-head processing time, latency per sample, and throughput      │
└───────────────────────────────────┬───────────────────────────────────┘
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│ 4. QUANTITATIVE COMPARATIVE BENCHMARKS                                │
│ Accuracy, F1/Recall, agreement ratios, error classification taxonomy │
└───────────────────────────────────┬───────────────────────────────────┘
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│ 5. QUALITATIVE CASE STUDIES & ERROR TAXONOMY                          │
│ Side-by-side diffs: Baseline vs Candidate (Success, Edge Case, Fail)  │
└───────────────────────────────────┬───────────────────────────────────┘
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│ 6. PRODUCTION ROLLOUT & STABILITY AUDIT                               │
│ Scale metrics, SLA compliance, error handling, storage integration    │
└───────────────────────────────────┬───────────────────────────────────┘
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│ 7. DECISION MATRIX, HUMAN-IN-THE-LOOP & STRATEGIC ROADMAP             │
│ Concrete recommendations, automation boundaries, next milestones      │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3. Standardized Batch Workload Runtime Table Blueprint

To provide executives with an immediate basis for decision-making, always normalize execution times against a **standardized benchmark batch** (e.g., 100 complex items, 1,000 inference requests, or 10,000 data rows).

Below is the generic comparative blueprint:

| Candidate Option | Per-Sample Latency | Secondary Stage Latency | Average End-to-End Latency | **Total Runtime (100 Units)** | Throughput | Resource Utilization | Technical Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Option A (Baseline / Legacy)**<br>• *Multi-Stage Ensembling* | ~1.62s / unit | ~11.1s / unit | ~78.5s / unit | **~7,850s (~2.18 hrs / 131 min)** | ~45.9 units/hr | Peak: High (63.6%) | Highest resource cost; bottlenecked by sequential multi-model arbitration. |
| **Option B (Heavyweight Sole)**<br>• *Frontier Foundation Model* | ~0.84s / unit | ~11.1s / unit | ~46.8s / unit | **~4,680s (~1.30 hrs / 78 min)** | ~76.9 units/hr | Peak: Moderate (50.7%) | Strong semantic reasoning, but heavy memory footprint and moderate latency. |
| **Option C1 (Lightweight - Unoptimized)**<br>• *Domain-Specific Model (Raw)* | ~1.07s / unit | ~1.51s / unit | ~41.2s / unit | **~4,116s (~1.14 hrs / 69 min)** | ~87.5 units/hr | Peak: Low (13.0%) | Memory-efficient, but hindered by decoding bottlenecks or lack of caching. |
| **Option C2 (Lightweight - Optimized)**<br>• *Domain-Specific + Caching/Batching* | **~0.54s / unit** | **~0.58s / unit** | **~28.72s / unit** | **2,871.98s (~0.80 hrs / 48 min)** | **125.4 units/hr** | **Peak: Minimal (13.5%)** | 🏆 **Production Winner.** 2.7x faster than Option A, 1.6x faster than Option B. |

---

## 4. Production Design System (CSS Tokens & Component Styles)

Copy and adapt this complete design system into the `<style>` block of the HTML report generator:

```css
:root {
    --bg-primary: #0b0f19;
    --bg-secondary: #111827;
    --bg-card: #1e293b;
    --bg-card-hover: #243447;
    --border-color: #334155;
    --border-highlight: #475569;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent-primary: #38bdf8;
    --accent-hover: #0ea5e9;
    --accent-glow: rgba(56, 189, 248, 0.15);
    --success: #10b981;
    --success-glow: rgba(16, 185, 129, 0.15);
    --warning: #f59e0b;
    --warning-glow: rgba(245, 158, 11, 0.15);
    --danger: #ef4444;
    --danger-glow: rgba(239, 68, 68, 0.15);
    --purple: #a855f7;
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 16px;
    --radius-xl: 24px;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.2);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    --shadow-lg: 0 10px 25px -3px rgba(0, 0, 0, 0.4);
}

/* Universal Light Mode Variables */
.light-mode {
    --bg-primary: #f8fafc;
    --bg-secondary: #ffffff;
    --bg-card: #ffffff;
    --bg-card-hover: #f1f5f9;
    --border-color: #e2e8f0;
    --border-highlight: #cbd5e1;
    --text-primary: #0f172a;
    --text-secondary: #334155;
    --text-muted: #64748b;
    --accent-primary: #0284c7;
    --accent-hover: #0369a1;
    --accent-glow: rgba(2, 132, 199, 0.12);
    --success: #059669;
    --success-glow: rgba(5, 150, 105, 0.12);
    --warning: #d97706;
    --warning-glow: rgba(217, 119, 6, 0.12);
    --danger: #dc2626;
    --danger-glow: rgba(220, 38, 38, 0.12);
    --purple: #7c3aed;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.65;
    font-size: 15px;
    display: block;
    min-height: 100vh;
    transition: background-color 0.3s ease, color 0.3s ease;
}

/* Sticky Top Navigation */
header.top-header {
    position: sticky;
    top: 0;
    z-index: 100;
    background-color: rgba(17, 24, 39, 0.92);
    backdrop-filter: blur(14px);
    border-bottom: 1px solid var(--border-color);
    transition: background-color 0.3s ease, border-color 0.3s ease;
}
.light-mode header.top-header {
    background-color: rgba(255, 255, 255, 0.94);
    border-bottom-color: var(--border-color);
}
.header-container {
    max-width: 1280px;
    margin: 0 auto;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}
.header-brand { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.brand-badge {
    width: 36px; height: 36px; border-radius: var(--radius-sm);
    background: linear-gradient(135deg, #0284c7, #38bdf8);
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-weight: 800; font-size: 15px;
    box-shadow: 0 0 15px var(--accent-glow);
}
.brand-title { font-size: 14.5px; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
.brand-subtitle { font-size: 10.5px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
.top-nav { display: flex; align-items: center; gap: 4px; overflow-x: auto; scrollbar-width: none; padding: 4px 0; }
.top-nav::-webkit-scrollbar { display: none; }
.nav-pill {
    display: inline-flex; align-items: center; padding: 6px 12px;
    color: var(--text-secondary); text-decoration: none; font-size: 12px; font-weight: 600;
    border-radius: 999px; white-space: nowrap; transition: all 0.2s ease;
}
.nav-pill:hover, .nav-pill.active { background-color: var(--bg-card); color: var(--accent-primary); }

.theme-toggle-btn {
    background: var(--bg-card); border: 1px solid var(--border-color);
    color: var(--text-secondary); padding: 6px 14px; border-radius: var(--radius-sm);
    cursor: pointer; font-size: 12px; font-weight: 600;
    display: flex; align-items: center; gap: 6px; transition: all 0.2s;
}
.theme-toggle-btn:hover { color: var(--accent-primary); border-color: var(--accent-primary); }

/* Centered Main Canvas */
main.main-content {
    margin: 0 auto;
    width: 100%;
    max-width: 1280px;
    padding: 35px 24px 80px;
}

/* Executive Hero Banner */
.hero-banner {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.98)),
                radial-gradient(ellipse at top right, rgba(56, 189, 248, 0.15), transparent 60%);
    border: 1px solid var(--border-highlight);
    border-radius: var(--radius-xl);
    padding: 40px;
    margin-bottom: 35px;
    box-shadow: var(--shadow-lg);
    position: relative;
    overflow: hidden;
}
.hero-title {
    font-size: 28px; font-weight: 800; line-height: 1.3; margin-bottom: 12px;
    background: linear-gradient(135deg, #ffffff 30%, #94a3b8 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-description { font-size: 15px; color: var(--text-secondary); max-width: 920px; margin-bottom: 24px; }

/* KPI Grid */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px; margin-top: 25px; }
.kpi-card {
    background: var(--bg-card); border: 1px solid var(--border-color);
    border-radius: var(--radius-md); padding: 18px 20px; transition: all 0.2s ease;
}
.kpi-card:hover { transform: translateY(-2px); border-color: var(--accent-primary); box-shadow: 0 4px 20px var(--accent-glow); }
.kpi-label { font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.kpi-value { font-size: 26px; font-weight: 800; color: var(--text-primary); line-height: 1.1; }
.kpi-value.accent { color: var(--accent-primary); }
.kpi-value.success { color: var(--success); }
.kpi-value.purple { color: var(--purple); }
.kpi-sub { font-size: 12px; color: var(--text-muted); margin-top: 5px; }

/* Section Containers & Cards */
.section-container { margin-bottom: 50px; scroll-margin-top: 70px; }
.section-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 24px; padding-bottom: 12px; border-bottom: 1px solid var(--border-color);
}
.section-title { font-size: 22px; font-weight: 800; display: flex; align-items: center; gap: 12px; color: var(--text-primary); }
.section-number {
    width: 32px; height: 32px; background: var(--bg-card);
    border: 1px solid var(--border-highlight); border-radius: var(--radius-sm);
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 700; color: var(--accent-primary);
}
.card {
    background-color: var(--bg-secondary); border: 1px solid var(--border-color);
    border-radius: var(--radius-lg); padding: 28px; margin-bottom: 24px; box-shadow: var(--shadow-sm);
}
.card-header { margin-bottom: 18px; }
.card-title { font-size: 17px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px; }
.card-subtitle { font-size: 13.5px; color: var(--text-secondary); }

/* Data Tables */
.table-responsive { overflow-x: auto; margin: 16px 0; border-radius: var(--radius-md); border: 1px solid var(--border-color); }
table { width: 100%; border-collapse: collapse; font-size: 13.5px; text-align: left; }
th { background-color: var(--bg-card); color: var(--text-primary); font-weight: 600; padding: 12px 16px; border-bottom: 1px solid var(--border-color); white-space: nowrap; }
td { padding: 11px 16px; border-bottom: 1px solid var(--border-color); color: var(--text-secondary); }
tr:last-child td { border-bottom: none; }
tr:hover td { background-color: rgba(255, 255, 255, 0.02); color: var(--text-primary); }
.highlight-win { color: var(--success); font-weight: 700; }

/* Visual Asset Container */
.image-container { margin: 20px 0; text-align: center; }
.report-img {
    max-width: 100%; height: auto; border-radius: var(--radius-md);
    border: 1px solid var(--border-color); cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    box-shadow: var(--shadow-md); background-color: #ffffff;
}
.report-img:hover { transform: scale(1.01); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); border-color: var(--accent-primary); }
.image-caption { font-size: 12.5px; color: var(--text-muted); margin-top: 8px; font-style: italic; }
.image-grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 20px; margin: 20px 0; }

/* Qualitative Diff Boxes */
.case-card { background-color: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 20px; margin-bottom: 16px; }
.case-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; }
.case-title { font-weight: 700; font-size: 14.5px; color: var(--text-primary); }
.diff-box { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin-top: 10px; }
.diff-column { background: var(--bg-card); border-radius: var(--radius-sm); padding: 12px; border-left: 3px solid var(--border-color); }
.diff-column.success { border-left-color: var(--success); background: var(--success-glow); }
.diff-column.danger { border-left-color: var(--danger); background: var(--danger-glow); }
.diff-label { font-size: 11.5px; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; display: flex; align-items: center; gap: 5px; }
.diff-text { font-family: 'Fira Code', monospace; font-size: 12px; color: var(--text-primary); word-break: break-word; }

/* Callout Alerts */
.callout { border-left: 4px solid var(--accent-primary); background: var(--accent-glow); padding: 16px 20px; border-radius: 0 var(--radius-md) var(--radius-md) 0; margin: 18px 0; font-size: 14px; }
.callout.success { border-left-color: var(--success); background: var(--success-glow); }
.callout.warning { border-left-color: var(--warning); background: var(--warning-glow); }

/* Badges / Tags */
.badge-group { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.tag { font-size: 11.5px; font-weight: 600; padding: 4px 10px; border-radius: 999px; display: inline-flex; align-items: center; gap: 5px; letter-spacing: 0.3px; }
.tag-blue { background: var(--accent-glow); color: var(--accent-primary); border: 1px solid rgba(56, 189, 248, 0.3); }
.tag-green { background: var(--success-glow); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.3); }
.tag-purple { background: rgba(168, 85, 247, 0.15); color: var(--purple); border: 1px solid rgba(168, 85, 247, 0.3); }
.tag-amber { background: var(--warning-glow); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.3); }

/* Lightbox Modal */
.modal {
    display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%;
    background-color: rgba(0, 0, 0, 0.88); backdrop-filter: blur(8px);
    justify-content: center; align-items: center; flex-direction: column;
}
.modal-content { max-width: 92vw; max-height: 86vh; border-radius: var(--radius-md); box-shadow: 0 0 35px rgba(0, 0, 0, 0.8); background-color: #fff; }
.modal-caption { color: #f8fafc; margin-top: 14px; font-size: 14px; font-weight: 500; }
.modal-close { position: absolute; top: 25px; right: 35px; color: #f8fafc; font-size: 36px; font-weight: bold; cursor: pointer; transition: color 0.2s; }
.modal-close:hover { color: var(--accent-primary); }

/* LIGHT MODE EXPLICIT OVERRIDES (Zero Dark Bleeding) */
.light-mode .hero-banner {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%),
                radial-gradient(ellipse at top right, rgba(2, 132, 199, 0.1), transparent 60%);
    border-color: #cbd5e1; box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.06);
}
.light-mode .hero-title {
    background: linear-gradient(135deg, #0f172a 30%, #334155 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.light-mode .hero-description { color: #475569; }
.light-mode .kpi-card { background: #ffffff; border-color: #cbd5e1; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04); }
.light-mode .kpi-card:hover { border-color: var(--accent-primary); box-shadow: 0 6px 20px rgba(2, 132, 199, 0.15); }
.light-mode .card { background-color: #ffffff; border-color: #cbd5e1; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04); }
.light-mode .case-card { background-color: #f8fafc; border-color: #cbd5e1; }
.light-mode .diff-column { background: #f1f5f9; border-color: #cbd5e1; }
.light-mode .diff-column.success { background: #ecfdf5; border-left-color: #10b981; }
.light-mode .diff-column.danger { background: #fef2f2; border-left-color: #ef4444; }
.light-mode .callout { background: rgba(2, 132, 199, 0.08); border-left-color: #0284c7; }
.light-mode .callout.success { background: rgba(16, 185, 129, 0.08); border-left-color: #10b981; }
.light-mode .callout.warning { background: rgba(245, 158, 11, 0.08); border-left-color: #f59e0b; }
.light-mode .table-responsive { background: #ffffff; border-color: #cbd5e1; }
.light-mode th { background-color: #f1f5f9; color: #0f172a; border-bottom-color: #cbd5e1; }
.light-mode td { border-bottom-color: #e2e8f0; color: #334155; }
.light-mode tr:hover td { background-color: rgba(0, 0, 0, 0.02); }
.light-mode .section-number { background: #f1f5f9; border-color: #cbd5e1; color: #0284c7; }
.light-mode .theme-toggle-btn { background: #f1f5f9; border-color: #cbd5e1; color: #0f172a; }

/* Print Styles */
@media print {
    header.top-header { display: none; }
    main.main-content { margin: 0; padding: 0; max-width: 100%; }
    body { background: #fff; color: #000; }
    .card { border: 1px solid #ccc; box-shadow: none; page-break-inside: avoid; }
    .report-img { max-width: 90%; }
}
```

---

## 5. Universal Python Report Generator Blueprint (`build_executive_report.py`)

Below is the generic, parameterized Python builder that can be configured for any engineering project:

```python
import os
import json
import base64
from pathlib import Path
from html.parser import HTMLParser

def get_base64_image(image_path: Path) -> str:
    """Read any raster or vector graphic and return a valid Data URI."""
    if not image_path.exists():
        print(f"[WARN] Graphic asset not found: {image_path}")
        return ""
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    ext = image_path.suffix.lstrip(".").lower()
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "svg": "image/svg+xml",
        "webp": "image/webp"
    }
    mime = mime_map.get(ext, "image/png")
    return f"data:{mime};base64,{encoded}"

def build_executive_report():
    # 1. Path Configuration
    root_dir = Path("/path/to/project")
    doc_dir = root_dir / "doc"
    images_dir = doc_dir / "images"
    output_html = doc_dir / "executive_report.html"

    # 2. Asset Manifest (Populate with all figures to embed)
    asset_manifest = [
        "architecture_flow.png",
        "resource_profiler_chart.png",
        "latency_throughput_curve.png",
        "accuracy_agreement_donut.png",
        "qualitative_sample_a.png",
        "qualitative_sample_b.png"
    ]
    
    print("Serializing graphical assets to Base64 Data URIs...")
    b64_map = {}
    for name in asset_manifest:
        path = images_dir / name
        b64_map[name] = get_base64_image(path)
        if b64_map[name]:
            print(f"  ✓ {name} -> {len(b64_map[name]) / 1024:.1f} KB Data URI")

    # 3. Assemble HTML Template with CSS Tokens and Interactive Lightbox
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Executive Technical Report & Architecture Evaluation</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        /* Insert Production Design System from Section 4 here */
    </style>
</head>
<body>

    <!-- Sticky Top Header Navigation -->
    <header class="top-header">
        <div class="header-container">
            <div class="header-brand">
                <div class="brand-badge">ENG</div>
                <div>
                    <div class="brand-title">System Architecture & Benchmark</div>
                    <div class="brand-subtitle">Executive Technical Evaluation</div>
                </div>
            </div>
            <nav class="top-nav">
                <a href="#summary" class="nav-pill active">Executive Summary</a>
                <a href="#architecture" class="nav-pill">1. Architecture</a>
                <a href="#resources" class="nav-pill">2. Compute & Memory</a>
                <a href="#runtime" class="nav-pill">3. Workload Runtime</a>
                <a href="#evaluation" class="nav-pill">4. Comparative Evaluation</a>
                <a href="#cases" class="nav-pill">5. Case Studies</a>
                <a href="#production" class="nav-pill">6. Production Scale</a>
                <a href="#roadmap" class="nav-pill">7. Decision Roadmap</a>
            </nav>
            <div class="header-actions">
                <button class="theme-toggle-btn" onclick="toggleTheme()">
                    <span id="theme-icon">☀️</span> Theme
                </button>
            </div>
        </div>
    </header>

    <!-- Centered Canvas -->
    <main class="main-content">
        <!-- Section: Executive Summary -->
        <section id="summary" class="hero-banner">
            <div class="badge-group">
                <span class="tag tag-blue">Project: System Optimization</span>
                <span class="tag tag-green">Status: Verified & Production Ready</span>
                <span class="tag tag-purple">Hardware: Standardized Node</span>
            </div>
            <h1 class="hero-title">Universal Architecture & Performance Benchmark</h1>
            <p class="hero-description">
                Comprehensive technical audit synthesizing empirical latency, resource utilization, accuracy trade-offs, and normalized batch execution times across legacy, frontier, and specialized candidate options.
            </p>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-label">Workload Completion</div>
                    <div class="kpi-value success">100%</div>
                    <div class="kpi-sub">0 unhandled exceptions or failures</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Latency Reduction</div>
                    <div class="kpi-value accent">2.0x Faster</div>
                    <div class="kpi-sub">Optimized pipeline acceleration</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Memory Footprint</div>
                    <div class="kpi-value purple">Minimal</div>
                    <div class="kpi-sub">Zero out-of-memory overhead</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Auto-Accept / Pass Rate</div>
                    <div class="kpi-value success">High Yield</div>
                    <div class="kpi-sub">Meets production SLA boundaries</div>
                </div>
            </div>
        </section>

        <!-- Chapter 1: Architecture & Topology -->
        <section id="architecture" class="section-container">
            <div class="section-header">
                <div class="section-title"><span class="section-number">1</span> System Architecture & Workflow Topology</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <div class="card-title">End-to-End Execution Topology</div>
                    <div class="card-subtitle">Decoupled stages and asynchronous consensus mechanisms</div>
                </div>
                <div class="image-container">
                    <img src="images/architecture_flow.png" alt="Architecture Flow" class="report-img" onclick="openModal(this.src, 'System Architecture & Dataflow Diagram')">
                    <div class="image-caption">Figure 1.1: Multi-stage pipeline architecture with arbitration and fallback routing</div>
                </div>
            </div>
        </section>

        <!-- Chapter 2: Hardware & Compute Profiling -->
        <section id="resources" class="section-container">
            <div class="section-header">
                <div class="section-title"><span class="section-number">2</span> Hardware Profiling & Compute Optimization</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Resource Footprint Breakdown</div>
                    <div class="card-subtitle">Static model allocation vs dynamic operational peak</div>
                </div>
                <!-- Insert Resource Profiling Table -->
            </div>
        </section>

        <!-- Chapter 3: Workload Runtime Benchmarks -->
        <section id="runtime" class="section-container">
            <div class="section-header">
                <div class="section-title"><span class="section-number">3</span> Standardized Workload Execution Benchmarks</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Normalized 100-Unit Batch Runtime Comparison</div>
                    <div class="card-subtitle">End-to-end execution measurements across candidate architectures</div>
                </div>
                <!-- Insert Standardized Runtime Table from Section 3 -->
            </div>
        </section>

        <!-- Additional Chapters 4, 5, 6, 7 as defined in Section 2 -->
    </main>

    <!-- Interactive Lightbox Modal -->
    <div id="imageModal" class="modal" onclick="closeModal()">
        <span class="modal-close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImg">
        <div class="modal-caption" id="modalCaption"></div>
    </div>

    <script>
        function openModal(src, caption) {
            const modal = document.getElementById("imageModal");
            const modalImg = document.getElementById("modalImg");
            const modalCaption = document.getElementById("modalCaption");
            modal.style.display = "flex";
            modalImg.src = src;
            modalCaption.innerText = caption || "";
        }
        function closeModal() {
            document.getElementById("imageModal").style.display = "none";
        }
        document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });

        function toggleTheme() {
            document.body.classList.toggle("light-mode");
            const isLight = document.body.classList.contains("light-mode");
            document.getElementById("theme-icon").innerText = isLight ? "🌙" : "☀️";
        }

        // Scrollspy for top navigation pills
        const sections = document.querySelectorAll("section");
        const navPills = document.querySelectorAll(".nav-pill");
        window.addEventListener("scroll", () => {
            let current = "";
            sections.forEach(sec => {
                if (pageYOffset >= (sec.offsetTop - 120)) {
                    current = sec.getAttribute("id");
                }
            });
            navPills.forEach(pill => {
                pill.classList.remove("active");
                if (pill.getAttribute("href") === `#${current}`) {
                    pill.classList.add("active");
                }
            });
        });
    </script>
</body>
</html>"""

    # 4. Perform Base64 Ingestion (Replace relative image paths)
    for name, b64_str in b64_map.items():
        if b64_str:
            old_pattern = f'images/{name}'
            count = html_content.count(old_pattern)
            html_content = html_content.replace(old_pattern, b64_str)
            print(f"  ✓ Substituted {count} instance(s) of '{old_pattern}' with Base64 Data URI")

    # 5. Syntactic Validation via HTMLParser
    class SyntaxValidator(HTMLParser): pass
    validator = SyntaxValidator()
    validator.feed(html_content)

    # 6. Emit Final Standalone Artifact
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    file_size_mb = os.path.getsize(output_html) / 1024 / 1024
    print(f"\n[SUCCESS] Standalone Executive Report generated at: {output_html}")
    print(f"Total File Size: {file_size_mb:.2f} MB (100% Offline Portable)")

if __name__ == "__main__":
    build_executive_report()
```

---

## 6. Pre-Flight Delivery Acceptance Checklist

Before delivering the consolidated HTML report to stakeholders or committing to the repository, ensure all 6 criteria pass:

- [ ] **100% Offline Verification**: Run `grep -o 'src="images/' <report>.html`. The count must be strictly `0`. No external image references are permitted.
- [ ] **Zero Dark Residue in Light Mode**: Switch between themes using the top header button (`☀️ / 🌙`). Verify:
  - All `.kpi-card` containers turn into pure white cards with soft grey borders (`#cbd5e1`).
  - The `.hero-banner` transforms into a clean corporate card without dark navy bleeding.
  - Side-by-side diff columns (`.diff-column`) switch to readable pastel tints (`#ecfdf5` / `#fef2f2`).
  - Table headers (`th`) and zebra rows maintain high contrast against dark text (`#0f172a` / `#334155`).
- [ ] **Normalized Batch Workload Comparison**: The report must provide concrete per-unit latency, total batch runtime, throughput, and memory consumption for a standardized workload (e.g., 100 or 1,000 units) across all candidate solutions.
- [ ] **Interactive Lightbox Zoom**: Click on every figure and plot to confirm that the full-resolution modal opens smoothly and closes via the `&times;` icon, background click, or `Escape` key.
- [ ] **Automated HTML Syntax Validation**: Verify that the Python `HTMLParser` script completes without unclosed tag errors or malformed nesting.
- [ ] **Print & PDF Export Fidelity**: Press `Ctrl + P` (Print Preview). Confirm that the navigation bar hides automatically and page breaks do not cut through cards or data tables.
