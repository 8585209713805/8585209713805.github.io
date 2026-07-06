#!/bin/bash
# 法规笔记 · 一键发布批注到网站（GitHub Pages）
# 用法:
#   ./publish_note.sh          发布 ~/Downloads 里最新导出的笔记批注
#   ./publish_note.sh --dry    只预览将要做什么，不提交/不推送
#
# 工作流程（用户侧）:
#   1) 在浏览器打开笔记，编辑条文解读/四色批注（自动存本机浏览器）
#   2) 点笔记右上角「导出」→ 文件下载到 ~/Downloads（文件名含日期）
#   3) 对 AI 说「发布批注」→ AI 运行本脚本 → 自动替换 notes/ 并推送公网
#
# 脚本逻辑: 扫描 ~/Downloads/*学习笔记_*.html，去掉文件名里的 _YYYYMMDD，
# 得到网站 notes/ 下的目标文件名；存在则覆盖，不存在则跳过（需先用技能生成登记）。

set -e
SITE_DIR="$(cd "$(dirname "$0")" && pwd)"
NOTES_DIR="$SITE_DIR/notes"
DOWNLOADS="$HOME/Downloads"
DRY=""
[[ "$1" == "--dry" ]] && DRY=1

# 收集导出文件，按修改时间从旧到新（保证同名笔记最终用最新那份）
files=()
while IFS= read -r f; do [ -n "$f" ] && files+=("$f"); done < <(ls -tr "$DOWNLOADS"/*学习笔记_*.html 2>/dev/null || true)

if [ ${#files[@]} -eq 0 ]; then
  echo "未在 $DOWNLOADS 找到导出的笔记（*学习笔记_*.html）。请先在浏览器点「导出」。"
  exit 0
fi

echo "找到 ${#files[@]} 个导出文件，将按时间顺序发布（同名取最新）："
published=()
for f in "${files[@]}"; do
  base="$(basename "$f")"
  target="$(echo "$base" | sed -E 's/_[0-9]{8}\.html$/.html/')"
  dest="$NOTES_DIR/$target"
  if [ ! -f "$dest" ]; then
    echo "  ⚠ 跳过 $base -> notes/$target 不存在（该笔记尚未在网站登记，请先用技能生成）"
    continue
  fi
  if [ -n "$DRY" ]; then
    echo "  [dry] 将复制 $base -> notes/$target"
  else
    cp "$f" "$dest"
    echo "  ✔ 已更新 notes/$target （来自 $base）"
  fi
  published+=("$target")
done

if [ -n "$DRY" ]; then
  echo "[dry] 不执行 git 提交与推送。"
  exit 0
fi

if [ ${#published[@]} -eq 0 ]; then
  echo "没有可发布的笔记。"
  exit 0
fi

cd "$SITE_DIR"
echo "发布批注: ${published[*]}"
python3 "$SITE_DIR/sync_to_github.py"
echo "✔ 已通过 GitHub API 同步，公网约 1-3 分钟后生效："
echo "   https://8585209713805.github.io/"
for p in "${published[@]}"; do
  echo "   https://8585209713805.github.io/notes/$p"
done
