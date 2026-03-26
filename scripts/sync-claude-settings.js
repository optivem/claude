#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const GLOBAL_SETTINGS = path.join(
  process.env.USERPROFILE || process.env.HOME,
  ".claude",
  "settings.json"
);
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

const g = writeJsonIfChanged(GLOBAL_SETTINGS, newGlobal, global);
const p = writeJsonIfChanged(PROJECT_SETTINGS, newProject, project);

if (g || p) {
  console.log("Settings synced.");
} else {
  console.log("Settings already in sync.");
}
