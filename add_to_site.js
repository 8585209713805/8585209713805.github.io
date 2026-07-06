#!/usr/bin/env node
/*
 * 法规学习笔记 · 网站自动登记脚本
 * 用法: node add_to_site.js <笔记HTML路径> [标题] [副标题] [领域] [标签逗号分隔]
 *   - 脚本所在目录即网站根目录（__dirname），复制笔记到 notes/ 并写入 index.html 的 SITE_NOTES。
 *   - 标题/副标题/领域优先取命令行参数；缺省时从笔记文件提取（兼容 LAW_TITLE/LAW_SUB/LAW_FIELD 与早期静态 <h1>/<small> 写法）。
 *   - 已登记过同一文件则跳过，避免重复。
 */
const fs = require('fs');
const path = require('path');

const SITE_DIR = __dirname;
const NOTES_DIR = path.join(SITE_DIR, 'notes');
const INDEX = path.join(SITE_DIR, 'index.html');
const MARKER = '// === AUTO-INSERT-MARKER ===';
const DEFAULT_TAGS = ['条文解读','关联法条','分层笔记','速查卡','关联案例','自测模式'];

function extract(re, s){ const m = s.match(re); return m ? m[1].trim() : ''; }
function escQuotes(s){ return (s || '').replace(/"/g, '\\"'); }

function main(){
  const args = process.argv.slice(2);
  const file = args[0];
  if(!file){ console.error('用法: node add_to_site.js <笔记HTML路径> [标题] [副标题] [领域] [标签逗号分隔]'); process.exit(1); }
  if(!fs.existsSync(file)){ console.error('笔记文件不存在:', file); process.exit(1); }
  const html = fs.readFileSync(file, 'utf8');

  let title = args[1]
    || extract(/const LAW_TITLE\s*=\s*['"]([^'"]+)['"]/, html)
    || extract(/<h1>《?([^<》]+?)学习笔记/, html);
  let sub = args[2]
    || extract(/const LAW_SUB\s*=\s*['"]([^'"]+)['"]/, html)
    || extract(/<small>([^<]+)<\/small>/, html);
  let cat = args[3]
    || extract(/const LAW_FIELD\s*=\s*['"]([^'"]+)['"]/, html)
    || '其他';
  let tags = args[4]
    ? args[4].split(',').map(t => t.trim()).filter(Boolean)
    : DEFAULT_TAGS;

  if(!title){ console.error('无法从文件提取法规名，请显式传入标题参数'); process.exit(1); }
  if(!sub) sub = '';

  const base = path.basename(file);
  fs.mkdirSync(NOTES_DIR, { recursive: true });
  fs.copyFileSync(file, path.join(NOTES_DIR, base));
  console.log('已复制笔记到 notes/', base);

  if(!fs.existsSync(INDEX)){ console.error('未找到 index.html:', INDEX); process.exit(1); }
  let idx = fs.readFileSync(INDEX, 'utf8');
  if(!idx.includes(MARKER)){ console.error('index.html 缺少登记标记', MARKER); process.exit(1); }

  // 去重：同一文件已登记则跳过
  if(idx.includes('file:"notes/' + base + '"') || idx.includes("file:'notes/" + base + "'")){
    console.log('该笔记已登记，跳过（如需更新请先手动删除旧条目）。');
    process.exit(0);
  }

  const entry =
    '  {title:"' + escQuotes(title) + '", sub:"' + escQuotes(sub) + '", file:"notes/' + base +
    '", tags:[' + tags.map(t => '"' + escQuotes(t) + '"').join(',') +
    '], cat:"' + escQuotes(cat) + '"},\n  ' + MARKER;

  idx = idx.replace(MARKER, entry);
  fs.writeFileSync(INDEX, idx, 'utf8');
  console.log('已在 index.html 登记：', title, '· 领域：', cat);
}

main();
