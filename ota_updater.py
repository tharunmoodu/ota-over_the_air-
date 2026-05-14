#!/usr/bin/env python3

import subprocess
import time
import os
import sys
import logging
import threading

REPO_DIR      = os.path.dirname(os.path.abspath(__file__))
APP_SCRIPT    = os.path.join(REPO_DIR, "app.py")
POLL_INTERVAL = 30
BRANCH        = "main"
LOG_FILE      = os.path.join(REPO_DIR, "ota_updater.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [OTA] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

app_process = None

def run(cmd):
    result = subprocess.run(cmd, shell=True, cwd=REPO_DIR,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return result.stdout.strip(), result.returncode

def get_local_commit():
    out, _ = run(f"git rev-parse {BRANCH}")
    return out

def get_remote_commit():
    run(f"git fetch origin {BRANCH}")
    out, _ = run(f"git rev-parse origin/{BRANCH}")
    return out

def pull_latest():
    log.info("Pulling latest code...")
    out, code = run(f"git pull origin {BRANCH}")
    log.info(out)
    return code == 0

def log_app_output(proc):
    for line in proc.stdout:
        log.info(f"[APP] {line.rstrip()}")

def start_app():
    global app_process
    stop_app()
    log.info("Starting app.py ...")
    app_process = subprocess.Popen(
        [sys.executable, "-u", APP_SCRIPT],
        cwd=REPO_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    log.info(f"App running with PID {app_process.pid}")
    threading.Thread(target=log_app_output, args=(app_process,), daemon=True).start()

def stop_app():
    global app_process
    if app_process and app_process.poll() is None:
        log.info(f"Stopping app PID {app_process.pid}")
        app_process.terminate()
        try:
            app_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            app_process.kill()
        app_process = None

def main():
    log.info("=" * 50)
    log.info("  OTA Updater started")
    log.info(f"  Repo     : {REPO_DIR}")
    log.info(f"  Branch   : {BRANCH}")
    log.info(f"  Interval : {POLL_INTERVAL}s")
    log.info("=" * 50)

    start_app()

    while True:
        try:
            time.sleep(POLL_INTERVAL)
            log.info("Checking for updates...")
            local  = get_local_commit()
            remote = get_remote_commit()
            if local == remote:
                log.info(f"Already up to date ({local[:8]})")
            else:
                log.info(f"Update found! {local[:8]} → {remote[:8]}")
                if pull_latest():
                    log.info("✅ Update applied! Restarting app...")
                    start_app()
                else:
                    log.error("❌ git pull failed. Will retry next cycle.")
        except KeyboardInterrupt:
            log.info("OTA Updater stopped.")
            stop_app()
            sys.exit(0)
        except Exception as e:
            log.error(f"Error: {e}")

if __name__ == "__main__":
    main()
