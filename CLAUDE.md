# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

REBA (Rapid Entire Body Assessment) ergonomic analysis tool using MediaPipe pose estimation and a PySide6 GUI. Analyzes real-time camera or video files to calculate joint angles, compute REBA scores, and assess workplace ergonomic risk levels.

## Commands

```bash
# Install dependencies (uses uv package manager)
uv sync

# Run the application
python src/reba_tool/MediaPipeApp.py

# Format code
black src/

# Lint
flake8 src/

# Run tests
pytest
```

Python version: 3.11 (pinned in `.python-version`)

## Architecture

The application follows a pipeline: **Video Input → Pose Detection → Angle Calculation → REBA Scoring → Risk Display/Export**

### Core Modules (`src/reba_tool/`)

- **`MediaPipeApp.py`** — Main GUI application (PySide6/Qt6). Contains `MainWindow`, `VideoProcessThread` (background video processing via QThread), `TableCDialog` (REBA Table C lookup), and `UIConfig` (centralized UI parameters). This is the entry point.

- **`angle_calculator.py`** — `AngleCalculator` class. Converts MediaPipe 33-landmark pose data into joint angles (neck, trunk, upper arm, forearm, wrist, legs) using 3D coordinate geometry. Filters landmarks by visibility threshold (>0.5).

- **`reba_scorer.py`** — `REBAScorer` class. Implements the complete REBA method: body part scoring from angles, Table A (trunk+neck+legs), Table B (upper arm+forearm+wrist), Table C (cross-reference), adjustment factors (load, grip, activity), and 5-level risk classification with color coding.

- **`data_logger.py`** — `DataLogger`, `OnlineStats`, `StatisticsAccumulator`. Records per-frame results and exports to CSV, JSON, or Markdown. Uses Welford's algorithm for O(1) memory streaming statistics. Has optional pandas dependency (graceful degradation if absent).

### Data Flow

```
MainWindow
  └─ VideoProcessThread (QThread)
       ├─ cv2.VideoCapture → frames
       ├─ mediapipe.Holistic → pose landmarks
       ├─ AngleCalculator.calculate_all_angles(landmarks)
       ├─ REBAScorer.calculate_reba(angles)
       ├─ DataLogger.add_frame_result(...)
       └─ Signal → MainWindow (UI update)
```

### Module Import Convention

Modules use direct imports (not package-relative): `from angle_calculator import AngleCalculator`. The application is run directly from the `src/reba_tool/` directory.

### Variant Files

`MediaPipeApp -table.py` and `MediaPipeApp - raw.py` are earlier/alternative versions of the main app. The canonical version is `MediaPipeApp.py`.

## Key Technical Details

- **REBA Tables**: Table A is 5x3x2 (trunk x neck x legs), Table B is 6x2x3 (upper arm x forearm x wrist), Table C is 12x12 (Score A x Score B). All implemented as nested lists in `reba_scorer.py`.
- **Risk Levels**: 1=Negligible(green), 2-3=Low(light green), 4-7=Medium(yellow), 8-10=High(orange), 11-15=Very High(red).
- **GUI threading**: Video processing runs on `QThread` with Qt signals for frame/result updates to keep the UI responsive.
- **Chinese text rendering**: Uses bundled `Arial.Unicode.ttf` (23MB) via PIL for Chinese overlay text on video frames.
- **Results output**: Saved to `results/` directory in CSV or JSON format.
- **Docstrings and comments are in Traditional Chinese** (繁體中文).
