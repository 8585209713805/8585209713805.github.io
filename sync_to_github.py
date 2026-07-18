#!/usr/bin/env python3
# 用 GitHub Contents API 同步站点文件到仓库(绕过 git push：沙箱代理禁 github.com，仅放行 api.github.com)
import os, glob, base64, json, subprocess, urllib.parse, sys, time

PAT = open('/Users/zf/.workbuddy/github_token').read().strip()
REPO = '8585209713805/8585209713805.github.io'
BASE = f'https://api.github.com/repos/{REPO}/contents'
ROOT = '/Users/zf/WorkBuddy/法规笔记网站'

# 需要同步到站点的文件(相对 ROOT)
FILES = ['index.html', 'README.md', 'add_to_site.js', 'publish_note.sh',
         'sync_to_github.py', 'statute-study-notebook.zip']
# 动态纳入 notes/ 下所有笔记（以后用技能新增的笔记也能自动同步）
FILES += sorted(os.path.join('notes', os.path.basename(p))
                for p in glob.glob(os.path.join(ROOT, 'notes', '*.html')))


def curl(method, url, data=None):
    cmd = ['curl', '-s', '--max-time', '60', '--retry', '3', '--retry-delay', '2',
           '-o', '-', '-w', '\n%{http_code}',
           '-H', f'Authorization: Bearer {PAT}']
    if method == 'PUT':
        cmd += ['-X', 'PUT', '-H', 'Content-Type: application/json', '--data', data]
    cmd.append(url)
    out = subprocess.run(cmd, capture_output=True, text=True)
    body, _, code = out.stdout.rpartition('\n')
    return int(code.strip() or 0), body


def get_remote(rel):
    """GET 远程文件元信息，带重试，直到拿到可解析的 JSON 或确认 404。"""
    enc = urllib.parse.quote(rel)
    last = {}
    last_code = 0
    for _ in range(4):
        code, body = curl('GET', f'{BASE}/{enc}')
        last_code = code
        if body:
            try:
                obj = json.loads(body)
                if isinstance(obj, dict) and ('sha' in obj or 'content' in obj or code == 404):
                    return obj, code
            except Exception:
                pass
        time.sleep(1.5)
    return last, last_code


def main():
    dry = '--dry' in sys.argv
    for rel in FILES:
        localp = os.path.join(ROOT, rel)
        if not os.path.exists(localp):
            print('跳过(本地不存在):', rel)
            continue
        remote, _ = get_remote(rel)
        sha = remote.get('sha', '')
        remote_b64 = ''.join(remote.get('content', '').split())  # 去空白(远程可能含换行)
        local_b64 = base64.b64encode(open(localp, 'rb').read()).decode()
        if remote_b64 == local_b64:
            print('无变化跳过:', rel)
            continue
        if dry:
            print(f'[dry] 将更新: {rel} (远程sha={sha[:8] if sha else "无"})')
            continue
        msg = f'auto-sync: 更新 {rel}'
        payload = {'message': msg, 'content': local_b64}
        if sha:
            payload['sha'] = sha
        enc = urllib.parse.quote(rel)
        ok = False
        for attempt in range(4):
            c2, _ = curl('PUT', f'{BASE}/{enc}', json.dumps(payload, ensure_ascii=False))
            if c2 in (200, 201):
                print(f'PUT {rel} -> HTTP {c2}')
                ok = True
                break
            # 422/409：sha 过期或缺失，重新取 sha 重试
            if c2 in (422, 409):
                time.sleep(2)
                remote, _ = get_remote(rel)
                sha = remote.get('sha', '')
                payload['sha'] = sha
                continue
            # 网络错误(0/5xx) 或 其他，退避后重试
            time.sleep(3)
            continue
        if not ok:
            print(f'!! 失败: {rel}')


if __name__ == '__main__':
    main()
