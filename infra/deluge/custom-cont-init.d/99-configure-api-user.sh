#!/usr/bin/with-contenv bash
# RPC + Web UI credentials are applied after Deluge starts (custom-services.d/configure-credentials).
# cont-init runs before the daemon, so /config/auth does not exist yet on first boot.
echo "[deluge-init] Credential bootstrap deferred until Deluge daemon is running"
