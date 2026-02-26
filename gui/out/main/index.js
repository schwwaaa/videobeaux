"use strict";
const electron = require("electron");
const path = require("path");
const url = require("url");
const child_process = require("child_process");
const fs = require("fs");
const os = require("os");
const crypto = require("crypto");
const __filename$1 = url.fileURLToPath(require("url").pathToFileURL(__filename).href);
const __dirname$1 = path.dirname(__filename$1);
const VB_ROOT = path.join(__dirname$1, "../../..");
function createWindow() {
  const mainWindow = new electron.BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: "#141414",
    titleBarStyle: process.platform === "darwin" ? "hiddenInset" : "default",
    webPreferences: {
      preload: path.join(__dirname$1, "../preload/index.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });
  if (process.env["ELECTRON_RENDERER_URL"]) {
    mainWindow.loadURL(process.env["ELECTRON_RENDERER_URL"]);
  } else {
    mainWindow.loadFile(path.join(__dirname$1, "../renderer/index.html"));
  }
  return mainWindow;
}
electron.app.whenReady().then(() => {
  const win = createWindow();
  electron.ipcMain.handle("dialog:openFile", async (_, filters) => {
    const result = await electron.dialog.showOpenDialog(win, {
      properties: ["openFile"],
      filters: filters || [
        { name: "Videos", extensions: ["mp4", "mov", "avi", "mkv", "webm", "mts", "mpg", "mpeg"] },
        { name: "All Files", extensions: ["*"] }
      ]
    });
    return result.filePaths[0] || null;
  });
  electron.ipcMain.handle("dialog:openDirectory", async () => {
    const result = await electron.dialog.showOpenDialog(win, {
      properties: ["openDirectory", "createDirectory"],
      buttonLabel: "Select Folder"
    });
    return result.filePaths[0] || null;
  });
  electron.ipcMain.handle("dialog:saveFile", async (_, { defaultName, filters }) => {
    const result = await electron.dialog.showSaveDialog(win, {
      defaultPath: defaultName || "output.mp4",
      filters: filters || [
        { name: "MP4 Video", extensions: ["mp4"] },
        { name: "MOV Video", extensions: ["mov"] },
        { name: "AVI Video", extensions: ["avi"] },
        { name: "All Files", extensions: ["*"] }
      ]
    });
    return result.filePath || null;
  });
  electron.ipcMain.handle("programs:discover", () => {
    return new Promise((resolve) => {
      const python = path.join(VB_ROOT, ".venv", "Scripts", "python.exe");
      const fallback = process.platform === "win32" ? "python" : "python3";
      const interpreter = fs.existsSync(python) ? python : fallback;
      const script = path.join(VB_ROOT, "gui", "discover_programs.py");
      let output = "";
      const proc = child_process.spawn(interpreter, [script], {
        cwd: VB_ROOT,
        env: { ...process.env, PYTHONUTF8: "1", PYTHONIOENCODING: "utf-8" },
        windowsHide: true
      });
      proc.stdout.on("data", (d) => {
        output += d.toString("utf8");
      });
      proc.on("close", (code) => {
        if (code === 0) {
          try {
            resolve(JSON.parse(output));
          } catch {
            resolve({});
          }
        } else {
          resolve({});
        }
      });
      proc.on("error", () => resolve({}));
    });
  });
  function getTempExt(outputType) {
    switch (outputType) {
      case "audio":
        return ".wav";
      case "json":
        return ".json";
      case "image":
        return ".png";
      case "text":
        return ".txt";
      default:
        return ".mp4";
    }
  }
  function findPython() {
    const venvPython = process.platform === "win32" ? path.join(VB_ROOT, ".venv", "Scripts", "python.exe") : path.join(VB_ROOT, ".venv", "bin", "python");
    if (fs.existsSync(venvPython)) return venvPython;
    return process.platform === "win32" ? "python" : "python3";
  }
  const STAT_LINE_RE = /\bframe=\s*\d+/;
  function runStep(python, args, cwd, sender) {
    return new Promise((resolve, reject) => {
      const proc = child_process.spawn(python, args, {
        cwd,
        env: { ...process.env, PYTHONUNBUFFERED: "1", PYTHONUTF8: "1", PYTHONIOENCODING: "utf-8" },
        windowsHide: true
      });
      currentProcess = proc;
      proc.stdout.on("data", (data) => {
        sender.send("log:message", { text: data.toString("utf8"), type: "stdout" });
      });
      let stderrBuf = "";
      const flushStderr = (isFinal) => {
        const parts = stderrBuf.split(/[\r\n]+/);
        stderrBuf = isFinal ? "" : parts.pop() ?? "";
        const normal = [];
        for (const line of parts) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          if (STAT_LINE_RE.test(trimmed)) {
            sender.send("log:message", { text: trimmed, type: "progress" });
          } else {
            normal.push(line);
          }
        }
        if (normal.length > 0) {
          sender.send("log:message", { text: normal.join("\n") + "\n", type: "stderr" });
        }
      };
      proc.stderr.on("data", (data) => {
        stderrBuf += data.toString("utf8");
        flushStderr(false);
      });
      proc.on("close", (code) => {
        if (stderrBuf.trim()) flushStderr(true);
        currentProcess = null;
        if (code === 0) resolve();
        else reject(new Error(`Process exited with code ${code}`));
      });
      proc.on("error", (err) => {
        currentProcess = null;
        if (err.code === "ENOENT") {
          reject(new Error(`Python not found. Make sure "python" or "python3" is on your PATH.`));
        } else {
          reject(err);
        }
      });
    });
  }
  let currentProcess = null;
  electron.ipcMain.on("pipeline:run", async (event, pipeline) => {
    const { inputPath, outputPath, steps } = pipeline;
    const python = findPython();
    const tempFiles = [];
    const log = (text, type = "system") => event.sender.send("log:message", { text, type });
    log(`videobeaux pipeline — ${steps.length} step(s)
`);
    log(`Input:  ${inputPath}
`);
    log(`Output: ${outputPath}

`);
    let currentInput = inputPath;
    try {
      for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        const isLast = i === steps.length - 1;
        const ext = getTempExt(step.outputType);
        const currentOutput = isLast ? outputPath : path.join(os.tmpdir(), `vb_${crypto.randomUUID()}${ext}`);
        if (!isLast) tempFiles.push(currentOutput);
        const args = [
          "-m",
          "videobeaux.cli",
          "-P",
          step.program,
          "-i",
          currentInput,
          "-o",
          currentOutput,
          "-F"
          // always overwrite temp + final output
        ];
        for (const [key, value] of Object.entries(step.args || {})) {
          const v = String(value).trim();
          if (v !== "" && v !== "false") {
            if (v === "true") {
              args.push(`--${key}`);
            } else {
              args.push(`--${key}`, v);
            }
          }
        }
        log(`── Step ${i + 1} / ${steps.length}: ${step.program}
`);
        log(`   ${python} ${args.join(" ")}

`, "command");
        await runStep(python, args, VB_ROOT, event.sender);
        log(`
✓ Step ${i + 1} complete

`);
        currentInput = currentOutput;
      }
      log(`
✓ Pipeline complete → ${outputPath}
`, "success");
      event.sender.send("pipeline:complete", { outputPath });
    } catch (err) {
      log(`
✗ ${err.message}
`, "error");
      event.sender.send("pipeline:error", { message: err.message });
    } finally {
      for (const f of tempFiles) {
        try {
          if (fs.existsSync(f)) fs.unlinkSync(f);
        } catch {
        }
      }
    }
  });
  electron.ipcMain.on("pipeline:cancel", () => {
    if (currentProcess) {
      currentProcess.kill("SIGTERM");
      currentProcess = null;
    }
  });
  electron.app.on("activate", () => {
    if (electron.BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});
electron.app.on("window-all-closed", () => {
  if (process.platform !== "darwin") electron.app.quit();
});
