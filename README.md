# Home Cook

A personal food management system for Ger's family, operated entirely through Claude Code.

## Tonight's Meal Server

A local HTTP server serves `tonights-meal.html` on the home network so the recipe can be viewed on a phone during cooking.

- **URL**: `http://192.168.4.200:9123/tonights-meal.html`
- **Port**: 9123 (chosen to avoid clashing with dev ports like 3000, 5173, 8080)
- **Managed by**: macOS `launchd` — starts automatically on boot, restarts if it crashes
- **Plist**: `~/Library/LaunchAgents/com.homecook.server.plist`
- **Logs**: `/tmp/homecook-server.log`
- **Serves from**: the repo root (`/Users/ger/Agents/Home-Cook`)

### Management commands

```bash
# Stop the server
launchctl unload ~/Library/LaunchAgents/com.homecook.server.plist

# Start the server
launchctl load ~/Library/LaunchAgents/com.homecook.server.plist

# Check logs
cat /tmp/homecook-server.log
```
