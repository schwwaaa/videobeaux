import json, sys
d = json.load(sys.stdin)
ok  = [k for k,v in d.items() if not v.get('error')]
err = [k for k,v in d.items() if v.get('error')]
print(f"OK: {len(ok)}  ERR: {len(err)}")

non_video = [(k,v) for k,v in d.items() if v.get('outputType','video') != 'video']
print(f"\nNon-video outputTypes ({len(non_video)}):")
for k,v in non_video:
    print(f"  {k}: {v['outputType']}")

print("\nErrors:")
for k,v in d.items():
    if v.get('error'):
        print(f"  {k}: {v['error']}")

print("\nSample long-flag fix (transcraibe args):")
t = d.get('transcraibe', {})
for arg in t.get('args', []):
    print(f"  {arg['name']} ({arg['type']}): {arg.get('label','')}")
