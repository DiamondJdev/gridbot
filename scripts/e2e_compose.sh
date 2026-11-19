#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
# Health is checked inside the container, so any free host port will do.
export GRIDBOT_HOST_PORT=0
compose=(docker compose -f "$root/docker/compose.yaml" -p "gridbot-e2e-$$")
profiles=(--profile runner --profile ros)
trap '"${compose[@]}" "${profiles[@]}" down --remove-orphans || exit 1' EXIT

"${compose[@]}" "${profiles[@]}" build
runner=$("${compose[@]}" --profile runner run --rm -T runner gridbot-run --version)
grep -Fx 'gridbot-run 0.1.0' <<< "$runner"
ros=$("${compose[@]}" --profile ros run --rm -T ros ros2 pkg list)
grep -Fx 'gridbot_msgs' <<< "$ros"
gateway=$("${compose[@]}" --profile runner run --rm -T gateway node dist/main.js --version)
grep -Fx 'gridbot-gateway 0.1.0' <<< "$gateway"

# Prints "sec.nanosec" once the gateway is connected and has a stamp.
health_js='fetch("http://127.0.0.1:8080/healthz").then((r) => r.json()).then((h) => {
  if (h.runtimeConnected && h.lastStamp) console.log(`${h.lastStamp.sec}.${h.lastStamp.nanosec}`);
}).catch(() => {})'

"${compose[@]}" --profile runner up -d runner gateway
first=""
for _ in $(seq 1 60); do
  stamp=$("${compose[@]}" --profile runner exec -T gateway node -e "$health_js" || true)
  if [[ -n "$stamp" && -z "$first" ]]; then
    first=$stamp
  elif [[ -n "$stamp" && "$stamp" != "$first" ]]; then
    echo "runtime connected, stamps advanced from $first to $stamp"
    exit 0
  fi
  sleep 0.5
done
echo "gateway never reported two different runtime stamps" >&2
"${compose[@]}" --profile runner logs runner gateway >&2
exit 1
