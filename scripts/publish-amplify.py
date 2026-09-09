import json, subprocess, urllib.request, zipfile, io, argparse

parser = argparse.ArgumentParser(description="Upload an existing React build to Amplify. Build with REACT_APP_API_URL first.")
parser.add_argument("app_id")
parser.add_argument("--branch", default="main")
parser.add_argument("--region", default="us-east-1")
args = parser.parse_args()

def aws(*command):
    return json.loads(subprocess.check_output(['aws', *command, '--region', args.region, '--output', 'json', '--no-cli-pager']))
from pathlib import Path
root = Path(__file__).resolve().parents[1] / 'client' / 'build'
if not (root / 'index.html').is_file():
    raise SystemExit('Run the frontend production build first.')
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in root.rglob('*'):
        if p.is_file() and not p.name.endswith('.map'):
            z.write(p, p.relative_to(root))
d = aws('amplify','create-deployment','--app-id',args.app_id,'--branch-name',args.branch)
r = urllib.request.Request(d['zipUploadUrl'], data=buf.getvalue(), method='PUT', headers={'Content-Type':'application/zip'})
with urllib.request.urlopen(r, timeout=60) as response:
    print('Upload HTTP', response.status)
j = aws('amplify','start-deployment','--app-id',args.app_id,'--branch-name',args.branch,'--job-id',d['jobId'])
print(json.dumps(j['jobSummary']))
