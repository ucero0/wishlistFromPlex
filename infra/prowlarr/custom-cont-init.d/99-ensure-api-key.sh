#!/usr/bin/with-contenv bash
# Apply PROWLARR_API_KEY from .env to config.xml before Prowlarr starts.
set -euo pipefail

CONFIG="/config/config.xml"
API_KEY="${PROWLARR_API_KEY:-}"

if [[ -z "$API_KEY" ]]; then
  echo "[prowlarr-init] WARNING: PROWLARR_API_KEY is not set. Set it in .env before first start." >&2
  exit 0
fi

if [[ ! -f "$CONFIG" ]]; then
  mkdir -p /config
  cat >"$CONFIG" <<EOF
<Config>
  <BindAddress>*</BindAddress>
  <Port>9696</Port>
  <SslPort>6969</SslPort>
  <EnableSsl>False</EnableSsl>
  <LaunchBrowser>True</LaunchBrowser>
  <ApiKey>${API_KEY}</ApiKey>
  <AuthenticationMethod>Forms</AuthenticationMethod>
  <AuthenticationRequired>DisabledForLocalAddresses</AuthenticationRequired>
  <Branch>master</Branch>
  <LogLevel>info</LogLevel>
  <SslCertPath></SslCertPath>
  <SslCertPassword></SslCertPassword>
  <UrlBase></UrlBase>
  <InstanceName>Prowlarr</InstanceName>
  <UpdateMechanism>Docker</UpdateMechanism>
</Config>
EOF
  echo "[prowlarr-init] Created config.xml with API key from .env"
  exit 0
fi

if grep -q "<ApiKey>" "$CONFIG"; then
  sed -i "s|<ApiKey>.*</ApiKey>|<ApiKey>${API_KEY}</ApiKey>|" "$CONFIG"
else
  sed -i "s|</Config>|  <ApiKey>${API_KEY}</ApiKey>\n</Config>|" "$CONFIG"
fi
echo "[prowlarr-init] config.xml API key synced from .env"
