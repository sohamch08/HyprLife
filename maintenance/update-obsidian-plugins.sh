#!/usr/bin/env bash
set -euo pipefail

# The official Obsidian CLI requires the app to be running.
vault=${1:-Research}
command -v obsidian >/dev/null || {
    printf 'Obsidian CLI is not available on PATH.\n' >&2
    exit 1
}

code=$(cat <<'JS'
(async () => {
  const plugins = app.plugins;
  if (typeof plugins.checkForUpdates !== "function" ||
      typeof plugins.installPlugin !== "function") {
    throw new Error("Obsidian plugin update API has changed.");
  }
  if (!navigator.onLine) throw new Error("Obsidian is offline.");

  // Obsidian logs registry-fetch failures instead of throwing them.
  const originalError = console.error;
  let checkFailed = false;
  console.error = (...args) => {
    checkFailed = true;
    originalError(...args);
  };
  try {
    await plugins.checkForUpdates(false);
  } finally {
    console.error = originalError;
  }
  if (checkFailed) throw new Error("Plugin update check failed; try again later.");

  const updates = Object.values(plugins.updates);
  const failed = [];
  for (const update of updates) {
    console.log(`Updating ${update.manifest.id} to ${update.version}...`);
    if (!await plugins.installPlugin(update.repo, update.version, update.manifest)) {
      failed.push(update.manifest.id);
    }
  }
  if (failed.length) throw new Error(`Failed to update: ${failed.join(", ")}`);
  console.log(updates.length ? `Updated ${updates.length} plugin(s).` : "No plugin updates reported.");
  return "TOPGRADE_OBSIDIAN_OK";
})()
JS
)

if output=$(obsidian "vault=$vault" eval "code=$code" 2>&1); then
    # eval can print an error while returning exit status zero.
    if printf '%s\n' "$output" | grep -qx '=> TOPGRADE_OBSIDIAN_OK'; then
        printf '%s\n' "$output" | sed '/^=> TOPGRADE_OBSIDIAN_OK$/d'
        exit 0
    fi
fi

printf '%s\n' "$output" >&2
printf 'Obsidian plugin update failed for vault "%s". Keep Obsidian open and check the error above.\n' "$vault" >&2
exit 1
