# ADR: Starlink Sensor Module

## Status
Accepted

## Context
Introduce Starlink observations as a dedicated sensor module without embedding Starlink logic in the Fusion Engine.

## Decision
- One module per sensor: lambda_sensors_starlink.py
- Public entry point: process()
- Standardized observation returned to Fusion
- Fusion orchestrates only

## Consequences
Clear boundaries, independent testing (Daytona), repeatable pattern for future sensors.