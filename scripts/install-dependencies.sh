#!/usr/bin/env bash
set -euo pipefail

# Keep a failed network attempt from consuming the whole crawler job.
# GitHub's step timeout is the outer limit for all three phases together.
retry_delay=${INSTALL_RETRY_DELAY_SECONDS:-5}
log=$(mktemp)
trap 'rm -f "$log"' EXIT

install_phase() {
  local label=$1 attempt rc
  shift
  for attempt in 1 2 3; do
    echo "Installing $label (attempt $attempt/3)"
    if timeout --kill-after=10s 150s "$@" >"$log" 2>&1; then
      cat "$log"
      return 0
    else
      rc=$?
    fi
    cat "$log"
    if [[ $attempt == 3 ]]; then
      echo "::error::Installation of $label failed after 3 attempts (exit $rc)."
      return "$rc"
    fi
    # Do not retry bad package versions, syntax errors, or arbitrary failures.
    if [[ $rc != 124 ]] && ! grep -Eiq \
      'Temporary failure (resolving|in name resolution)|Name or service not known|Could not resolve|Connection (reset|aborted)|ConnectionError|ReadTimeout|ConnectTimeout|Connection timed out|timed out|Network is unreachable|HTTP[^0-9]*50[0234]|50[0234] (Server Error|Bad Gateway|Service Unavailable|Gateway Timeout)' "$log"; then
      echo "::error::Installation of $label failed without a retryable network error (exit $rc)."
      return "$rc"
    fi
    echo "::warning::Temporary installation failure for $label; retrying in ${retry_delay}s."
    sleep "$retry_delay"
  done
}

install_phase pip python -m pip install --upgrade pip
install_phase packages python -m pip install -r requirements.txt
install_phase chromium python -m playwright install --with-deps chromium
