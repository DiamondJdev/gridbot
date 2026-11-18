# GitHub Actions

## What it does

Runs host checks on every pull request and push to `main`. ROS-related pull requests also build and test the Jazzy workspace.

## How it fits

Both workflows use Arm Linux and call the same [verification targets](../docs/testing.md) as local development.

## Running its tests

Run `make verify` and `make verify-ros` locally. Failed workflow steps upload their logs when logs exist.

## Main files

- [verify.yml](workflows/verify.yml) runs host checks.
- [verify-ros.yml](workflows/verify-ros.yml) runs colcon in Docker when relevant paths change.
