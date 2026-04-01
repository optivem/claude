#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const HOME = process.env.USERPROFILE || process.env.HOME;
const GLOBAL_SETTINGS = path.join(HOME, ".claude", "settings.json");
const GLOBAL_COMMANDS_DIR = path.join(HOME, ".claude", "commands");
const WORKSPACE_ROOT = path.join(__dirname, "..", "..");
const WORKSPACE_FILE = path.join(WORKSPACE_ROOT, "academy.code-workspace");
const PROJECT_SETTINGS = path.join(__dirname, "..", ".claude", "settings.json");
const PROJECT_COMMANDS_DIR = path.join(__dirname, "..", ".claude", "commands");

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
// Project is source of truth for hooks — push project hooks to global
if (project.hooks) {
  newGlobal.hooks = JSON.parse(JSON.stringify(project.hooks));
}

// Build the repo settings to distribute
const repoSettings = {
  permissions: {
    allow: mergedAllow,
    defaultMode: newProject.permissions.defaultMode,
  },
};
if (project.hooks) {
  repoSettings.hooks = JSON.parse(JSON.stringify(project.hooks));
}
if (global.skipDangerousModePermissionPrompt !== undefined) {
  repoSettings.skipDangerousModePermissionPrompt = global.skipDangerousModePermissionPrompt;
}

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

// Sync skills from claude/.claude/commands/ to ~/.claude/commands/
let skillCount = 0;
if (fs.existsSync(PROJECT_COMMANDS_DIR)) {
  fs.mkdirSync(GLOBAL_COMMANDS_DIR, { recursive: true });
  for (const file of fs.readdirSync(PROJECT_COMMANDS_DIR)) {
    const src = path.join(PROJECT_COMMANDS_DIR, file);
    const dest = path.join(GLOBAL_COMMANDS_DIR, file);
    const srcContent = fs.readFileSync(src, "utf-8");
    const destContent = fs.existsSync(dest) ? fs.readFileSync(dest, "utf-8") : null;
    if (srcContent !== destContent) {
      fs.writeFileSync(dest, srcContent, "utf-8");
      console.log(`  Updated skill: ${file}`);
      skillCount++;
    }
  }
}

if (g || p || repoCount > 0 || skillCount > 0) {
  console.log(`Settings synced (${repoCount} workspace repo(s), ${skillCount} skill(s) updated).`);
} else {
  console.log("Settings already in sync.");
}
