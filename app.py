import argparse
import subprocess
import re
import json
import requests
from datetime import datetime
import sys


# Webhook endpoint (default)
# https://hkdk.events/1mybf4xp0029un
# ENDPOINT = "https://be94b739c82dcf2a45dagt4jumryyyyyb.oast.pro"
ENDPOINT = "http://127.0.0.1:5013/webhook"

# File to store logs locally
LOG_FILE = "android_events.txt"


# Regex patterns to match both event types and capture the JSON object
patterns = [
    (re.compile(r'Single Event:\s*(\{.*\})'), 'Single Event'),
    (re.compile(r'Event Payload:\s*(\{.*\})'), 'Event Payload')
]


def send_raw(text: str, endpoint: str):
    """Send the exact matched text as plain text to the webhook."""
    try:
        resp = requests.post(endpoint, data=text.encode('utf-8'), headers={'Content-Type': 'text/plain'})
        return resp.status_code, resp.text
    except Exception as e:
        return None, str(e)


def send_json(obj: dict, endpoint: str):
    """Send the parsed JSON object to the webhook as JSON."""
    try:
        resp = requests.post(endpoint, json=obj)
        return resp.status_code, resp.text
    except Exception as e:
        return None, str(e)


def process_line(line: str, endpoint: str, mode: str):
    """Process a single decoded log line: match, log locally, and forward to endpoint.

    mode: 'raw' | 'json' | 'both'
    """
    for pattern, label in patterns:
        match = pattern.search(line)
        if not match:
            continue

        # Build a clean matched text using the human-readable label
        matched_text = f"{label}: {match.group(1)}"
        # timestamp for local log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Append to local log file using the same format you requested
        with open(LOG_FILE, "a") as f:
            f.write(f"{timestamp} | {matched_text}\n\n")

        # Try parse JSON for json mode
        parsed = None
        try:
            parsed = json.loads(match.group(1))
        except Exception:
            parsed = None

        results = []
        if mode in ("raw", "both"):
            status, body = send_raw(matched_text, endpoint)
            results.append(("raw", status, body))

        if mode in ("json", "both") and parsed is not None:
            status, body = send_json(parsed, endpoint)
            results.append(("json", status, body))

        # Print outcome(s)
        for kind, status, body in results:
            if status is None:
                print(f"❌ [{timestamp}] Failed to send ({kind}): {body}")
            else:
                name = parsed.get('eventName', 'unknown') if parsed else 'unknown'
                print(f"✅ [{timestamp}] Sent ({kind}) event '{name}' | Status: {status}")


def main():
    parser = argparse.ArgumentParser(description="Capture adb logcat events and forward to a webhook")
    parser.add_argument("--endpoint", "-e", default=ENDPOINT, help="Webhook endpoint URL")
    parser.add_argument("--mode", "-m", choices=["raw", "json", "both"], default="raw",
                        help="Send mode: raw (plain text), json (JSON body), or both")
    parser.add_argument("--stdin", action="store_true", help="Read test lines from stdin instead of adb")
    args = parser.parse_args()

    endpoint = args.endpoint
    mode = args.mode

    if args.stdin:
        print("📥 Reading lines from stdin (test mode). Send EOF (Ctrl+D) to stop.)")
        try:
            for line in sys.stdin:
                process_line(line.rstrip('\n'), endpoint, mode)
        except KeyboardInterrupt:
            print("\n🛑 Stopped (stdin).")
        return

    # Start reading adb logcat
    process = subprocess.Popen([
        "adb", "logcat"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)

    print("📡 Listening to adb logcat for events (Ctrl+C to stop)...")

    try:
        for raw in process.stdout:
            try:
                line = raw.decode("utf-8", errors="replace")
            except Exception:
                line = str(raw)

            process_line(line, endpoint, mode)

    except KeyboardInterrupt:
        print("\n🛑 Stopped listening.")
        process.terminate()


if __name__ == '__main__':
    main()
