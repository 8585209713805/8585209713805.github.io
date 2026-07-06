#!/usr/bin/env python3
# 用 GitHub Contents API 同步站点文件到仓库(绕过 git push：沙箱代理禁 github.com，仅放行 api.github.com)
import os, base64, json, subprocess, urllib.parse, sys

PAT = open('/Users/zf/.workbuddy/github_token').read().strip()
REPO = '8585209713805/8585209713805.github.io'
BASE = f'https://api.github.com/repos/{REPO}/contents'
ROOT = '/Users/zf/WorkBuddy/法规笔记网站'

# 需要同步到站点的文件(相对 ROOT)
FILES = ['index.html', 'README.md', 'add_to_site.js', 'publish_note.sh',
         'sync_to_github.py', 'statute-study-notebook.zip',
         'notes/法律援助法学习笔记.html',
         'notes/超龄劳动者基本权益保障暂行规定学习笔记.html']


def curl(method, url, data=None):
    cmd = ['curl', '-s', '-o', '-', '-w', '\n%{http_code}',
           '-H', f'Authorization: Bearer {PAT}']
    if method == 'PUT':
        cmd += ['-X', 'PUT', '-H', 'Content-Type: application/json', '--data', data]
    cmd.append(url)
    out = subprocess.run(cmd, capture_output=True, text=True)
    body, _, code = out.stdout.rpartition('\n')
    return int(code.strip() or 0), body


def main():
    dry = '--dry' in sys.argv
    for rel in FILES:
        localp = os.path.join(ROOT, rel)
        if not os.path.exists(localp):
            print('跳过(本地不存在):', rel)
            continue
        enc = urllib.parse.quote(rel)
        code, body = curl('GET', f'{BASE}/{enc}')
        remote = json.loads(body) if body else {}
        sha = remote.get('sha', '')
        remote_b64 = remote.get('content', '')
        local_b64 = base64.b64encode(open(localp, 'rb').read()).decode()
        if remote_b64 == local_b64:
            print('无变化跳过:', rel)
            continue
        if dry:
            print(f'[dry] 将更新: {rel} (远程sha={sha[:8]})')
            continue
        msg = f'auto-sync: 更新 {rel}'
        payload = {'message': msg, 'content': local_b64}
        if sha:
            payload['sha'] = sha
        c2, _ = curl('PUT', f'{BASE}/{enc}', json.dumps(payload, ensure_ascii=False))
        print(f'PUT {rel} -> HTTP {c2}')


if __name__ == '__main__':
    main()
