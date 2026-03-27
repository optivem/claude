#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const GLOBAL_SETTINGS = path.join(
  process.env.USERPROFILE || process.env.HOME,
  ".claude",
  "settings.json"
);
const WORKSPACE_ROOT = path.join(__dirname, "..", "..");
const WORKSPACE_FILE = path.join(WORKSPACE_ROOT, "academy.code-workspace");
const PROJECT_SETTINGS = path.join(__dirname, "..", ".claude", "settings.json");

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf-8"));
  } catch {
    return {};
  }
}

function writeJsonIfChanged(filePath, newData, oldData) {
  const newStr = JSON.stringify(newData, null, 2) + "\n";
  const oldStr = JSON.stringify(oldData, null, 2) + "\n";
  if (newStr !== oldStr) {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, newStr, "utf-8");
    return true;
  }
  return false;
}

function union(arr1, arr2) {
  const map = new Map();
  for (const entry of [...(arr1 || []), ...(arr2 || [])]) {
    const name = entry.replace(/\(.*\)$/, "");
    map.set(name, entry);
  }
  return [...map.values()];
}

// Merge global + project permissions
const global = readJson(GLOBAL_SETTINGS);
const project = readJson(PROJECT_SETTINGS);

const mergedAllow = union(
  global.permissions?.allow,
  project.permissions?.allow
);

const newGlobal = JSON.parse(JSON.stringify(global));
newGlobal.permissions = newGlobal.permissions || {};
newGlobal.permissions.allow = mergedAllow;

const newProject = JSON.parse(JSON.stringify(project));
newProject.permissions = newProject.permissions || {};
newProject.permissions.allow = mergedAllow;
if (global.permissions?.defaultMode) {
  newProject.permissions.defaultMode = global.permissions.defaultMode;
}

// Build the repo settings to distribute (permissions only, no hooks/other personal config)
const repoSettings = {
  permissions: {
    allow: mergedAllow,
    defaultMode: newProject.permissions.defaultMode,
  },
};

// Sync global and claude repo
const g = writeJsonIfChanged(GLOBAL_SETTINGS, newGlobal, global);
const p = writeJsonIfChanged(PROJECT_SETTINGS, newProject, project);

// Distribute to all workspace repos (skip claude — already done above)
const workspace = readJson(WORKSPACE_FILE);
const folders = workspace.folders || [];
let repoCount = 0;

for (const folder of folders) {
  const folderPath = folder.path || folder.name;
  if (folderPath === "claude") continue; // already handled
  const repoSettingsPath = path.join(
    WORKSPACE_ROOT,
    folderPath,
    ".claude",
    "settings.json"
  );
  const existing = readJson(repoSettingsPath);
  if (writeJsonIfChanged(repoSettingsPath, repoSettings, existing)) {
    console.log(`  Updated: ${folderPath}/.claude/settings.json`);
    repoCount++;
  }
}

if (g || p || repoCount > 0) {
  console.log(`Settings synced (${repoCount} workspace repo(s) updated).`);
} else {
  console.log("Settings already in sync.");
}
