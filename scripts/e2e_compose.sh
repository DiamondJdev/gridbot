#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
compose=(docker compose -f "$root/docker/compose.yaml" -p "gridbot-e2e-$$")
profiles=(--profile runner --profile ros)
trap '"${compose[@]}" "${profiles[@]}" down --remove-orphans || exit 1' EXIT

"${compose[@]}" "${profiles[@]}" build
runner=$("${compose[@]}" --profile runner run --rm -T runner)
grep -Fx 'gridbot-run 0.1.0' <<< "$runner"
ros=$("${compose[@]}" --profile ros run --rm -T ros ros2 pkg list)
grep -Fx 'gridbot_msgs' <<< "$ros"
gateway=$("${compose[@]}" --profile runner run --rm -T gateway)
grep -Fx 'gridbot-gateway 0.1.0' <<< "$gateway"
