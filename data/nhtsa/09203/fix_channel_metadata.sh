#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

pyisomme set "$script_dir/09203.mme" fine_location_3 TH -c '21*'
pyisomme set "$script_dir/09203.mme" fine_location_3 H3 -c '24*'
pyisomme set "$script_dir/09203.mme" unit um -c '??CHST??????DS??'
