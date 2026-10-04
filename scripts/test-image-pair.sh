#!/bin/bash
set -euo pipefail
if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  echo 'Usage: bash scripts/test-image-pair.sh BTC_IMAGE XBT_IMAGE KNOTS_BITCOIND [forward|forward-failure|reverse|reverse-failure|all]' >&2
  exit 2
fi
mode=${4:-all}
case "$mode" in forward|forward-failure|reverse|reverse-failure|all) ;; *) exit 2 ;; esac
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
backend=$(realpath -- "$3")
test -f "$backend" && test -x "$backend"
btc_image=$(docker image inspect --format '{{.Id}}' "$1")
xbt_image=$(docker image inspect --format '{{.Id}}' "$2")
prefix=$(mktemp -d /tmp/cln-pair-binaries.XXXXXX)
container=''
cleanup() {
  if [ -n "$container" ]; then docker rm -f "$container" >/dev/null 2>&1 || true; fi
  rm -rf -- "$prefix"
}
trap cleanup EXIT
# Copy installed binaries from the exact XBT image without starting it.
# CLN resolves its subdaemons and builtin plugins relative to its bin directory.
container=$(docker create --network none "$xbt_image")
docker cp "$container:/usr/local/." "$prefix/"
docker rm "$container" >/dev/null
container=''
results=$(mktemp -d /tmp/cln-image-pair.XXXXXX)
printf 'Disposable logs: %s\nBTC image: %s\nXBT image: %s\n' "$results" "$btc_image" "$xbt_image"
modes=("$mode")
if [ "$mode" = all ]; then modes=(forward forward-failure reverse reverse-failure); fi
for scenario in "${modes[@]}"; do
  docker run --rm --network none --init \
    -e BTC_XBT_DISPOSABLE_CONTAINER=1 \
    --mount "type=bind,src=$backend,dst=/test-bitcoind,readonly" \
    --mount "type=bind,src=$prefix,dst=/opt/xbt,readonly" \
    --mount "type=bind,src=$repo/tests/image_pair.py,dst=/image_pair.py,readonly" \
    --mount "type=bind,src=$results,dst=/results" \
    --entrypoint /usr/bin/python3 "$btc_image" /image_pair.py "$scenario"
done
