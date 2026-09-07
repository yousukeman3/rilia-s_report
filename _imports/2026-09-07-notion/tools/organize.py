"""2026-09-07 Notion export の初回整理用。編集済み資料への再実行は禁止。"""
from pathlib import Path
from urllib.parse import quote, unquote
import csv
import hashlib
import json
import os
import re

ROOT = Path(__file__).resolve().parents[3]
IMPORT = ROOT / '_imports/2026-09-07-notion'
RAW = IMPORT / 'raw'
BASE = RAW / 'リリアーナの魔術師自叙伝/作品設定資料集'
OUT = ROOT / '設定資料'

def read(p):
    return p.read_text(encoding='utf-8-sig')

def rows(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def name(p):
    return re.sub(r' [a-f0-9]{32}$', '', p.stem)

def filename(s):
    return s.replace('(主人公)', '').replace('：', '・') + '.md'

def href(p, target):
    return quote(Path(os.path.relpath(target, p.parent)).as_posix(), safe='/._-')

def link(p, target, label=None):
    return f'[{label or target.stem}]({href(p, target)})'

def write(p, body):
    if p.exists():
        raise FileExistsError(f'編集済み資料を上書きしません: {p}')
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body.rstrip() + '\n', encoding='utf-8')

db = {k: next(BASE.glob(k + ' *_all.csv')) for k in ['キャラクター', '作中用語', '登場魔術・魔法', '人間関係']}
characters = rows(db['キャラクター'])
terms = [r for r in rows(db['作中用語']) if not r['名前'].startswith('ダミー')]
spells = [r for r in rows(db['登場魔術・魔法']) if not r['名前'].startswith('ページ')]
relations = rows(db['人間関係'])
paths = {}
for r in characters:
    paths[r['名前']] = OUT / '人物' / filename(r['名前'])
for r in terms:
    folder = '世界観' if r['カテゴリ'] in ['地名', '家系', '組織', '種族'] or r['名前'] == 'アイテール界' else '魔術'
    paths[r['名前']] = OUT / folder / filename(r['名前'])
for r in spells:
    paths[r['名前']] = OUT / '魔術/術式' / filename(r['名前'])
ideas = sorted((RAW / 'リリアーナの魔術師自叙伝/ネタストック/temp ネタストックDB').glob('*.md'))
ideas += list((RAW / 'リリアーナの魔術師自叙伝/アイデアメモ').glob('錬金術アイデア出し *.md'))
for src in ideas:
    paths[name(src)] = OUT / '構想メモ' / filename(name(src))

sources = {}
dispositions = {}

def source(p, src, detail):
    sources.setdefault(p, []).append(src)
    dispositions.setdefault(src, []).append((p, detail))

def source_footer(p):
    return '\n## 出典\n\n' + '\n'.join('- ' + link(p, src, src.name) for src in dict.fromkeys(sources[p]))

def relation_name(value):
    return value.split(' (')[0]

def converted(value, p):
    # Notion CSV の「表示名 (相対パス)」を通常の Markdown リンクへ変換。
    for title in sorted(paths, key=len, reverse=True):
        value = re.sub(re.escape(title) + r' \([^\s]+\.(?:md|csv)\)', lambda m: link(p, paths[title], title), value)
    def replace(m):
        label, target = m.groups()
        label = label.strip()
        if label in paths:
            return link(p, paths[label], label)
        return label + '〔参照先未収録〕'
    return re.sub(r'([^,\n]+?) \(([^\s]+\.(?:md|csv))\)', replace, value)

def table(headers, values):
    def cell(v):
        return str(v).replace('|', '\\|').replace('\n', '<br>')
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |'] + ['| ' + ' | '.join(cell(v) for v in row) + ' |' for row in values])

labels = {
    'temp:作中用語とのリレーション（関連キャラ（出身地））': '出身地',
    'temp:作中用語とのリレーション（関連キャラ（出身家系））': '出身家系',
    'temp:作中用語とのリレーション（関連キャラ（在籍中））': '在籍先',
    'temp:作中用語とのリレーション（関連キャラ（種族））': '種族',
    'temp:作中用語とのリレーション（関連キャラ（過去に所属））': '過去の所属',
}
profiles = ['本名', 'よみがな', '別名', '性別', '年齢', '誕生日', '身長', '体重', '職業', *labels, '家族構成']
traits = ['一人称', '二人称', '性格', '台詞例', '趣味', '好きなもの', '嫌いなもの', '得意なこと', '苦手なこと']
magic = ['魂の大きさ', 'ソウルラダー', '魔力貯蔵', '属性転換', '付与特性', '生体調律', '使用魔術体系', '魔法体系', '愛', '歴史', '目', '行使階梯', '表現']
intro = {
    'リリアーナ・クレール(主人公)': '通称リリア。ココン村を襲った悪竜の事件を機に魔術師を志し、ローゼ＝フィアス魔術学園で学ぶ主人公。素直さと前へ進む力を持ち、複雑な操作よりも単純な魔力出力を得意とする。',
    'セリナ・アグラニオケ・スピーゲル': 'アグラニオケ一族の魔術師学生。五大制圧者（ファイブ・コンクェラー）の別名を持つ。良家の娘として高飛車に振る舞う一方、自己評価は低く、真面目な努力家である。',
    'フレア・クライヴ': '学園の何でも屋と呼ばれるハーフエルフの魔術師学生。本名欄はフレア・ガルドレア。世渡りのうまい自由人で、純化・精製を得意とする。人物関係ではリリアとセリナから「フレア先輩」と呼ばれる。',
    'ティリアシール・フリーマン': 'ローゼ＝フィアス魔術学園の学園長で、リリアの師。神殺しの魔術師、無幻の魔女、叙説の魔女などの別名を持つ。奔放な外面と、思慮深く自罰的な内面を併せ持つ。',
    'アリス・アグラニオケ・セイファート': '天体魔術を使用する魔術師・顧問魔術師。神殺しの魔術師、昇華の魔女などの別名を持つ。セリナからは叔母として敬われ、師ティリアシールには不信と尊敬が入り混じる。',
}

conflicts = []
for r in characters:
    title = r['名前']
    p = paths[title]
    src = next((BASE / 'キャラクター').glob(title + ' *.md'))
    source(p, db['キャラクター'], '人物プロフィール全フィールド')
    source(p, src, '本名・よみ・画像と元ページ')
    for child in sorted((BASE / 'キャラクター' / title).glob('*.csv')):
        child_rows = rows(child)
        for cr in child_rows:
            if cr.get('名前') == title:
                for key, value in cr.items():
                    if value and r.get(key) and relation_name(value) != relation_name(r[key]):
                        conflicts.append({'source': str(child.relative_to(RAW)), 'name': title, 'field': key, 'main': r[key], 'view': value})
                    elif value and not r.get(key):
                        r[key] = value
        source(p, child, 'プロフィール・関連術式・人物関係のビューを照合')
    body = f'# {title.replace("(主人公)", "")}\n\n[人物一覧](README.md) · [資料集の入口](../README.md)\n\n{intro[title]}\n\n> Notion設定資料の整理版。人物の秘密・将来の来歴を含む。空欄は未記載として扱う。\n'
    for section, keys in [('基本プロフィール', profiles), ('性格・話し方・嗜好', traits), ('魔術・魔法の資質', magic), ('来歴・その他', ['来歴', '概要', 'その他設定'])]:
        vals = [(labels.get(k, k), converted(r[k], p)) for k in keys if r.get(k)]
        if not vals:
            continue
        body += f'\n## {section}\n\n'
        if section in ['基本プロフィール', '魔術・魔法の資質']:
            body += table(['項目', '記載内容'], vals) + '\n'
        else:
            for k, v in vals:
                body += f'\n### {k}\n\n{v}\n'
    body += '\n## 人物関係\n\n' + link(p, OUT / '人物/人物関係.md', '誰が誰をどう見ているか（全16件・台詞全文）') + '\n\n'
    vals = []
    for rel in relations:
        a, b = relation_name(rel['Aは']), relation_name(rel['Bを'])
        if title in [a, b]:
            vals.append([converted(rel['Aは'], p), converted(rel['Bを'], p), rel['分類'], rel['何て呼んでる？']])
    body += table(['見る側', '相手', '分類', '呼び方'], vals) + '\n'
    known = [s for s in spells if relation_name(s.get('主な使用者', '')) == title]
    if known:
        body += '\n## 登録術式\n\n' + '\n'.join('- ' + link(p, paths[s['名前']], s['名前']) for s in known) + '\n'
    image_files = sorted((BASE / 'キャラクター' / title).glob('*.png'))
    if image_files:
        body += '\n## 画像資料\n\n'
        for img in image_files:
            source(p, img, '添付画像を原ファイルから参照')
            body += f'![{title}の添付画像]({href(p, img)})\n\n'
    if title.startswith('リリアーナ'):
        body += '\n## 照合メモ\n\n家族構成の「両親と暮らす一人っ子」は、第一話の父を失ったことを示す描写と時点の照合が必要。エーテルライン越えも来歴欄の記載であり、第一話時点の達成としては扱わない。詳しくは[要確認事項](../編集管理/要確認事項.md)を参照。\n'
    if title.startswith('フレア'):
        body += '\n## 名前の扱い\n\nページ名・呼称は「フレア・クライヴ」、本名欄は「フレア・ガルドレア」。双方を保持し、使い分けの理由は補完していない。\n'
    write(p, body + source_footer(p))

def normalize_body(text, src, p):
    lines = text.splitlines()
    # 冒頭のタイトルと Notion プロパティを除き、本文から始める。
    start = 1
    while start < len(lines) and (not lines[start].strip() or re.match(r'^(カテゴリ|よみ|作成日時):', lines[start])):
        start += 1
    lines = lines[start:]
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r'^#{1,6} (目次|関連項目)$', line):
            i += 1
            continue
        # Notion の複数行セルを通常の Markdown 表へ修復。
        if line.startswith('|') and not line.rstrip().endswith('|'):
            while i + 1 < len(lines) and not line.rstrip().endswith('|'):
                i += 1
                line += '<br>' + lines[i].strip()
        if re.match(r'^#{1,5} ', line):
            line = '#' + line
        result.append(line.rstrip())
        i += 1
    text = '\n'.join(result).replace('****[', '[')
    def resolve(m):
        label, target = m.groups()
        if target.startswith(('http:', 'https:', '#')):
            return m.group(0)
        candidate = (src.parent / unquote(target)).resolve()
        clean = name(candidate)
        if clean in paths:
            return link(p, paths[clean], label)
        if candidate.exists():
            return link(p, candidate, label)
        return label + '〔参照先未収録〕'
    return re.sub(r'\[([^\]]*)\]\(([^\s]+)\)', resolve, text).strip()

for r in terms:
    title = r['名前']
    p = paths[title]
    src = next((BASE / '作中用語').glob(title + ' *.md'), None)
    source(p, db['作中用語'], '用語・分類・関連情報')
    body = f'# {title}\n\n[資料集の入口](../README.md) · [用語索引](../用語索引.md)\n\n'
    body += table(['項目', '内容'], [(k, converted(v, p)) for k, v in r.items() if v and k != '名前']) + '\n'
    if src:
        source(p, src, '本文全体（見出し・表・リンクのみ整形）')
        content = normalize_body(read(src), src, p)
        if content:
            body += '\n' + content + '\n'
        else:
            body += '\n> 元ページは名前とカテゴリのみで、本文は未記載。\n'
        if title in ['自然魔術', '人工魔術', '神授魔術', '属性転換']:
            body += '\n関連する共通原理や行使手順は[魔術](魔術.md)に記載されている。この記事固有の定義は補完していない。\n'
    else:
        body += '\n> CSVに名称・分類・関連情報が残っている項目。個別ページの本文は今回のZIPに含まれていない。本文がもともと空だったかは不明。\n'
    if title in ['魔力', '魔術', '錬金術']:
        body += '\n## 読み合わせ\n\n[魔術体系の読み方](体系の読み方.md) · [要確認事項](../編集管理/要確認事項.md)\n'
    write(p, body + source_footer(p))

for r in spells:
    title = r['名前']
    p = paths[title]
    src = next((BASE / '登場魔術・魔法').glob(title + ' *.md'))
    source(p, db['登場魔術・魔法'], '術式の全登録フィールド')
    source(p, src, '個別ページと空欄状態を確認')
    body = f'# {title}\n\n[術式一覧](README.md) · [資料集の入口](../../README.md)\n\n'
    body += table(['項目', '内容'], [(k, converted(v, p)) for k, v in r.items() if v and k not in ['名前', '作成日時']])
    body += '\n\n## 効果・使用条件\n\n元ページの概要・詳細は空欄。名称や種別から具体的効果、射程、詠唱、制限を推定していない。数値の単位も原資料では未記載。\n'
    if title == '来るべき罪科の清算':
        body += '\nアイテールとエーテルが必要属性に併記されている。魔力本文の相性説明との関係は[要確認事項](../../編集管理/要確認事項.md)を参照。\n'
    write(p, body + source_footer(p))

rp = OUT / '人物/人物関係.md'
source(rp, db['人間関係'], '16件の方向・分類・呼称・心情・台詞を全文収録')
body = '# 人物関係\n\n[人物一覧](README.md) · [資料集の入口](../README.md)\n\n関係は「AがBをどう見るか」という方向を持つ。心情欄と台詞は人物の認識であり、対象人物や世界についての客観的な確定事項には置き換えない。\n\n'
body += table(['A（見る側）', 'B（相手）', '分類', '呼び方'], [(converted(r['Aは'], rp), converted(r['Bを'], rp), r['分類'], r['何て呼んでる？']) for r in relations]) + '\n'
for r in relations:
    a, b = relation_name(r['Aは']), relation_name(r['Bを'])
    body += f'\n## {a.replace("(主人公)", "")} → {b.replace("(主人公)", "")}\n\n分類：{r["分類"]} ／ 呼び方：{r["何て呼んでる？"]}\n\n' + r['どう思ってる？'] + '\n'
for src in (BASE / '人間関係').glob('*.md'):
    source(rp, src, '個別の人物関係ページ')
write(rp, body + source_footer(rp))

for src in ideas:
    p = paths[name(src)]
    source(p, src, '構想本文を保持')
    body = f'# {name(src)}\n\n[構想メモ一覧](README.md) · [資料集の入口](../README.md)\n\n> 原資料ではネタストック／アイデアメモに置かれていた構想。今回の整理で設定本文への採用を確定していない。\n\n'
    body += normalize_body(read(src), src, p) + '\n'
    write(p, body + source_footer(p))

# 全ファイルの行き先・保持理由。テンプレートは整理本文に混ぜず原文保存。
coverage = []
for src in sorted(RAW.rglob('*')):
    if not src.is_file():
        continue
    targets = dispositions.get(src, [])
    reason = '資料本文へ整理／照合に使用' if targets else '原文保存（索引・ビュー・テンプレート・空ページ）'
    if src.suffix == '.csv' and not targets:
        reason = '原文保存（データベースの一覧・重複ビュー）'
    coverage.append({'source': src.relative_to(RAW).as_posix(), 'disposition': reason, 'targets': sorted({p.relative_to(ROOT).as_posix() for p, _ in targets})})
(IMPORT / 'coverage.json').write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(IMPORT / 'view-conflicts.json').write_text(json.dumps(conflicts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(IMPORT / 'catalog.json').write_text(json.dumps({k: p.relative_to(ROOT).as_posix() for k, p in paths.items()}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'characters': len(characters), 'relations': len(relations), 'terms': len(terms), 'spells': len(spells), 'ideas': len(ideas), 'raw_files': len(coverage), 'view_conflicts': len(conflicts)}, ensure_ascii=False))
