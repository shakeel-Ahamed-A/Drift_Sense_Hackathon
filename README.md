# Drift-Sense
## Hybrid Localization of Semiconductor SEM Patterns

A computer-vision solution for recovering the location of a high-resolution
reference SEM pattern inside a lower-magnification search image.

## Problem

Reference:
1000 × 1000 px @ 1 nm/px

Search:
1000 × 1000 px @ 10 nm/px

The reference corresponds to approximately a 100 × 100 pixel region
in search-image coordinates.

## Solution

The system combines:

1. Multi-scale gradient NCC
2. Candidate generation
3. ORB + RANSAC geometric verification
4. Late confidence fusion
5. Center-of-image tie handling

## Repository Structure

...

## Installation

```bash
python -m venv .venv
