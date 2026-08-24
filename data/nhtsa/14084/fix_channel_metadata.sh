#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

pyisomme set "$script_dir/14084.mme" fine_location_3 H3 -c '11*'
pyisomme set "$script_dir/14084.mme" fine_location_3 HF -c '13*'
pyisomme set "$script_dir/14084.mme" unit um -c '??CHST??????DS??'
