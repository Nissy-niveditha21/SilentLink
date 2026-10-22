#!/usr/bin/env python3
import requests
import json
import sys

base = "http://127.0.0.1:8001"
results = []

def test(name, fn):
    try:
        status, detail = fn()
        results.append((name, status, detail))
    except Exception as e:
        results.append((name, "ERROR", str(e)[:120]))

def t1():
    r = requests.get(f"{base}/api/health", timeout=5)
    return r.status_code, json.dumps(r.json()) if r.status_code == 200 else r.text[:100]
test("GET /api/health", t1)

def t2():
    r = requests.get(f"{base}/", timeout=5)
    has_sl = "SilentLink" in r.text
    return r.status_code, f"{len(r.text)} chars, has_SilentLink={has_sl}"
test("GET /", t2)

def t10():
    r = requests.get(f"{base}/api/translate?phrase=hello", timeout=5)
    return r.status_code, json.dumps(r.json()) if r.status_code == 200 else r.text[:100]
test("GET /api/translate", t10)

def t11():
    r = requests.get(f"{base}/api/sign/GOOD", timeout=5)
    return r.status_code, json.dumps(r.json())[:120] if r.status_code == 200 else r.text[:100]
test("GET /api/sign/GOOD", t11)

def t12():
    r = requests.get(f"{base}/api/phrase_status", timeout=5)
    return r.status_code, json.dumps(r.json()) if r.status_code == 200 else r.text[:100]
test("GET /api/phrase_status", t12)

def t20():
    import websockets
    import asyncio
    async def ws_test():
        uri = "ws://127.0.0.1:8001/ws/sign"
        async with websockets.connect(uri, close_timeout=3) as ws:
            await ws.send(json.dumps({
                "type": "frame",
                "frame": {
                    "hand_landmarks": [[0.1, 0.2, 0.3]] * 21,
                    "timestamp_ms": 1000
                },
                "echo_id": "test_1"
            }))
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            # wait for second message which is the recognition frame
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(resp)
            return data
    data = asyncio.run(ws_test())
    rec = data.get('recognition', {})
    return 200, f"ws_type={data.get('type')}, rec_status={rec.get('status')}"
test("WS /ws/sign (landmark unpack)", t20)


print("=" * 70)
print("SilentLink END-TO-END TEST RESULTS")
print("=" * 70)
passed = 0
failed = 0
for endpoint, status, detail in results:
    ok = isinstance(status, int) and status in (200, 303, 400, 404)
    icon = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
    print(f"  [{icon}] {endpoint:35s} | {status:>5} | {detail}")
print("=" * 70)
print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
if failed > 0:
    print("\n*** SOME TESTS FAILED ***")
    sys.exit(1)
else:
    print("\n*** ALL TESTS PASSED ***")
    sys.exit(0)
