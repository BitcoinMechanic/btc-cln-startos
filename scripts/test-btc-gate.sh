#!/bin/bash
set -euo pipefail
if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
  echo 'Usage: bash scripts/test-btc-gate.sh IMAGE PATH_TO_KNOTS_BITCOIND [--fail]' >&2
  exit 2
fi
if [ "$#" -eq 3 ] && [ "$3" != '--fail' ]; then exit 2; fi
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
backend=$(realpath -- "$2")
test -f "$backend" && test -x "$backend"
results=$(mktemp -d /tmp/btc-image-gate.XXXXXX)
echo "Disposable logs: $results"
docker run --rm --network none --init \
  -e BTC_DISPOSABLE_CONTAINER=1 \
  --mount "type=bind,src=$backend,dst=/test-bitcoind,readonly" \
  --mount "type=bind,src=$repo/tests/image_gate.py,dst=/image_gate.py,readonly" \
  --mount "type=bind,src=$results,dst=/results" \
  --entrypoint /usr/bin/python3 "$1" /image_gate.py "${@:3}"
