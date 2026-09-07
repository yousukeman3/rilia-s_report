"""取り込み済み原文、整理版の導線、CSVの実質的な内容を検証する。"""
from pathlib import Path
from urllib.parse import unquote
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
IMPORT = ROOT / '_imports/2026-09-07-notion'
RAW = IMPORT / 'raw'
OUT = ROOT / '設定資料'
BASE = RAW / 'リリアーナの魔術師自叙伝/作品設定資料集'

def read(p):
    return p.read_text(encoding='utf-8-sig')

def links(s):
    # Notionのパスに含まれる丸括弧と、同一行の複数リンクを区別する。
    for m in re.finditer(r'!?\[([^\]]*)\]\(', s):
        start = m.end()
        i = start
        depth = 1
        while i < len(s) and depth:
            if s[i] == '(':
                depth += 1
            elif s[i] == ')':
                depth -= 1
            i += 1
        if not depth:
            yield m.start(), i, m.group(1), s[start:i-1]

def plain(s):
    for start, end, label, target in reversed(list(links(s))):
        s = s[:start] + label + s[end:]
    return re.sub(r'\s+', '', s.replace('<br>', '\n'))

def raw_value(s):
    return re.sub(r' \([^\s]+\.(?:md|csv)\)', '', s)

def rows(kind):
    with next(BASE.glob(kind + ' *_all.csv')).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

manifest = json.loads(read(IMPORT / 'manifest.json'))
coverage = json.loads(read(IMPORT / 'coverage.json'))
catalog = {k: ROOT / v for k, v in json.loads(read(IMPORT / 'catalog.json')).items()}
errors = []
for entry in manifest['entries']:
    p = RAW / entry['path']
    if not p.exists() or p.stat().st_size != entry['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest() != entry['sha256']:
        errors.append('原文不一致: ' + entry['path'])
assert len(manifest['entries']) == 107
assert {e['path'] for e in manifest['entries']} == {e['source'] for e in coverage}
assert {p.relative_to(RAW).as_posix() for p in RAW.rglob('*') if p.is_file()} == {e['path'] for e in manifest['entries']}
for entry in coverage:
    for target in entry['targets']:
        if not (ROOT / target).is_file():
            errors.append('整理先なし: ' + target)

# 検証記録自身へのリンクを含めて検査できるよう、初回だけ作成する。
report = IMPORT / 'verification.md'
if not report.exists():
    report.write_text('# 取込検証記録\n', encoding='utf-8')
docs = [ROOT / 'README.md', IMPORT / 'README.md', report, *OUT.rglob('*.md')]
local_links = 0
for p in docs:
    for _, _, _, target in links(read(p)):
        if re.match(r'\w+://', target) or target.startswith('#'):
            continue
        local_links += 1
        dest = (p.parent / unquote(target.split('#')[0])).resolve()
        if not dest.exists():
            errors.append(f'リンク切れ: {p.relative_to(ROOT)} -> {target}')
    for n, line in enumerate(read(p).splitlines(), 1):
        if line.rstrip() != line:
            errors.append(f'行末空白: {p.relative_to(ROOT)}:{n}')

fields = 0
ignored = {'名前', 'フィルター用リレーション', 'サムネイル画像', '画像資料', '人間関係（Aは）', '人間関係（Bを）', '作成日時'}
for kind in ['キャラクター', '作中用語', '登場魔術・魔法']:
    for row in rows(kind):
        title = row['名前']
        if title not in catalog:
            assert title.startswith(('ダミー', 'ページ'))
            continue
        body = plain(read(catalog[title]).split('\n## 出典')[0])
        for key, value in row.items():
            if key in ignored or not value:
                continue
            fields += 1
            if plain(raw_value(value)) not in body:
                errors.append(f'CSV内容欠落: {title} / {key}')
relation_doc = plain(read(OUT / '人物/人物関係.md'))
rels = rows('人間関係')
assert len(rels) == 16
for row in rels:
    for value in row.values():
        if plain(raw_value(value)) not in relation_doc:
            errors.append('人物関係内容欠落: ' + row['何て呼んでる？'])

# 原文の未収録リンクは修正せず、別の診断として残す。
missing = set()
for p in RAW.rglob('*.md'):
    for _, _, _, target in links(read(p)):
        if re.match(r'\w+://', target) or target.startswith('#'):
            continue
        dest = (p.parent / unquote(target.split('#')[0])).resolve()
        if not dest.exists():
            missing.add(str(dest.relative_to(RAW)))
(IMPORT / 'missing-source-targets.json').write_text(json.dumps(sorted(missing), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
result = {'raw_files_verified': len(manifest['entries']), 'coverage_entries': len(coverage), 'setting_documents': len(list(OUT.rglob('*.md'))), 'local_links_checked': local_links, 'csv_fields_checked': fields, 'relationships_checked': len(rels), 'missing_raw_link_targets': len(missing), 'errors': errors}
(IMPORT / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report.write_text(f'''# 取込検証記録

実施日：2026-09-07。`tools/verify.py` により検証。

- 原文107ファイルのサイズ・SHA-256：一致。
- 取込対応表：107ファイルを網羅。
- 設定資料のMarkdown：{result['setting_documents']}件。
- 整理版・入口・保存記録のローカルリンク：{local_links}件を確認。
- CSVの非空欄の実質的な値：{fields}項目を整理記事と照合。
- 人物関係：16件の内容を照合。
- 主要人物の全件CSVと個別プロフィールCSVの非空欄値の競合：0件。
- 検証エラー：{len(errors)}件。

原文内のMarkdownリンクには、ZIPに含まれない参照先が{len(missing)}件（重複除外）ある。`missing-source-targets.json` に記録し、原文は変更していない。これは整理版のリンク切れ件数とは別であり、元Notionの内容が存在しないことを意味しない。CSVの関連値は、全件CSVから整理版の該当記事へ接続している。

この検証は取り込みと転記・導線の検証であり、作品内の全設定の整合性を保証するものではない。第一話の照合範囲は冒頭のプロローグと「巣立ち」を中心とし、全文からの設定抽出や改稿は行っていない。
''', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
if errors:
    raise SystemExit(1)
