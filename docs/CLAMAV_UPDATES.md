# ClamAV and YARA Rules Update Configuration

## Overview

The ClamAV service is configured to automatically update:
- **ClamAV virus definitions**: Updated daily using `freshclam` (official ClamAV database)
- **YARA rules**: Updated daily from the [Yara-Rules/rules](https://github.com/Yara-Rules/rules) GitHub repository
- **Docker image**: Uses `clamav/clamav:latest` to always get the latest ClamAV version

## Update Schedule

- **Daily at 2 AM**: Automatic updates run via cron job
- **On container start**: YARA rules are initialized from GitHub if not present

## YARA Rules Repository

The service uses the most popular YARA rules repository:
- **Repository**: [Yara-Rules/rules](https://github.com/Yara-Rules/rules)
- **Branch**: `master`
- **Location**: `/yara-rules` inside the ClamAV container (mapped to `./yara-rules` on host)

### Features:
- ✅ Automatic clone on first run
- ✅ Daily updates via `git pull`
- ✅ Backup of existing rules before updates
- ✅ Automatic git installation if needed
- ✅ YARA scanning handled in ClamAV container (not in FastAPI)

## ClamAV Updates

### Virus Definitions
- Updated via `freshclam` (official ClamAV update tool)
- Connects to `database.clamav.net` mirror
- Updates run daily at 2 AM
- Daemon automatically reloaded after updates

### Docker Image
- Uses `clamav/clamav:latest` tag
- To update to latest image version:
  ```bash
  docker-compose pull clamav
  docker-compose up -d clamav
  ```

## Manual Updates

### Update ClamAV Definitions Manually
```bash
docker exec clamav freshclam
```

### Update YARA Rules Manually
```bash
docker exec clamav /usr/local/bin/update-antivirus.sh
```

### Force Re-clone YARA Rules
```bash
docker exec antivirus sh -c "rm -rf /yara-rules && git clone --depth 1 --branch master https://github.com/Yara-Rules/rules.git /yara-rules"
```

## Viewing Update Logs

```bash
# View update logs
docker exec antivirus tail -f /var/log/clamav-updates.log

# View last 50 lines
docker exec antivirus tail -n 50 /var/log/clamav-updates.log

# Check cron job status
docker exec antivirus crontab -l
```

## Architecture Note

**YARA scanning is handled in the ClamAV container**, not in FastAPI:
- YARA rules are stored in ClamAV container at `/yara-rules`
- HTTP scanning service (port 3311) handles both ClamAV and YARA scanning
- FastAPI calls the HTTP service - no YARA dependencies needed

See `docs/YARA_IN_CLAMAV_CONTAINER.md` for architecture details.

## Troubleshooting

### YARA Rules Not Updating

1. **Check if git is installed:**
   ```bash
   docker exec antivirus which git
   ```

2. **Check repository status:**
   ```bash
   docker exec antivirus sh -c "cd /yara-rules && git status"
   ```

3. **Manually test update:**
   ```bash
   docker exec antivirus /usr/local/bin/update-antivirus.sh
   ```

4. **Check network connectivity:**
   ```bash
   docker exec antivirus ping -c 3 github.com
   ```

### ClamAV Definitions Not Updating

1. **Check freshclam logs:**
   ```bash
   docker exec antivirus freshclam -v
   ```

2. **Check ClamAV daemon status:**
   ```bash
   docker exec antivirus clamdcheck.sh
   ```

3. **Verify database directory:**
   ```bash
   docker exec antivirus ls -la /var/lib/clamav/
   ```

### Container Not Starting

1. **Check container logs:**
   ```bash
   docker logs antivirus
   ```

2. **Verify script permissions:**
   ```bash
   docker exec antivirus ls -la /update-scripts/
   ```

3. **Test scripts manually:**
   ```bash
   docker exec antivirus /update-scripts/init-yara-rules.sh
   docker exec antivirus /update-scripts/setup-cron.sh
   ```

## Configuration Files

### Update Scripts Location
- Host: `./infra/clamav/update-scripts/`
- Container: `/update-scripts/`

### Scripts:
1. **`init-yara-rules.sh`**: Initializes YARA rules from GitHub on first run
2. **`update-antivirus.sh`**: Daily update script (runs via cron)
3. **`setup-cron.sh`**: Sets up the cron job for daily updates

### Logs Location
- Container: `/var/log/clamav-updates.log`
- View from host: `docker exec antivirus cat /var/log/clamav-updates.log`

## Summary

✅ **ClamAV definitions**: Auto-updated daily via `freshclam`  
✅ **YARA rules**: Auto-updated daily from GitHub (Yara-Rules/rules)  
✅ **Docker image**: Uses `:latest` tag (pull manually for updates)  
✅ **YARA in ClamAV**: All YARA scanning handled in ClamAV container  
✅ **Logs**: Available at `/var/log/clamav-updates.log`  
✅ **Manual updates**: Supported via docker exec commands
