#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_file, abort
import json
import pathlib
import datetime
import argparse
import re

app = Flask(__name__)

# File to store received events
FILE = pathlib.Path('received_events.jsonl')


def append_event(d):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    with FILE.open('a', encoding='utf-8') as f:
        # If the event is a raw string (matched payload), write it directly
        if isinstance(d, str):
            f.write(d.rstrip('\n') + '\n\n')
        else:
            f.write(json.dumps(d, ensure_ascii=False) + '\n\n')


@app.route('/webhook', methods=['POST'])
def webhook():
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    body_text = request.get_data(as_text=True)

    # If body contains an 'Event Payload: {json}' or 'Single Event: {json}', store just that matched text
    patterns = [
        (re.compile(r'Single Event:\s*(\{.*\})', re.DOTALL), 'Single Event'),
        (re.compile(r'Event Payload:\s*(\{.*\})', re.DOTALL), 'Event Payload')
    ]

    for pattern, label in patterns:
        m = pattern.search(body_text)
        if m:
            matched_text = f"{label}: {m.group(1)}"
            append_event(matched_text)
            return ('', 201)

    # Fallback: store full request details as JSON
    body_json = request.get_json(silent=True)
    event = {
        'timestamp': now,
        'method': request.method,
        'path': request.path,
        'args': request.args.to_dict(),
        'headers': dict(request.headers),
        'json': body_json,
        'text': body_text
    }
    append_event(event)
    return ('', 201)


@app.route('/events', methods=['GET'])
def events():
    if not FILE.exists():
        return jsonify([])
    out = []
    with FILE.open(encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                out.append({'raw': line})
    return jsonify(out)


@app.route('/events/download', methods=['GET'])
def download():
    if not FILE.exists():
        abort(404)
    return send_file(str(FILE.resolve()), mimetype='text/plain', as_attachment=True, download_name=FILE.name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=5012)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port)
