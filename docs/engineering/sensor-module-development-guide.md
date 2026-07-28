# Sensor Module Development Guide

## Contract
Each sensor module:
1. Owns parsing, validation, sensor-specific scoring, metadata
2. Exposes one public entry point (e.g. process())
3. Returns a standardized observation for the Fusion Engine
4. Does not write to DynamoDB, send alerts, or fuse scores