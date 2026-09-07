# Notion原資料 — 2026-09-07

[設定資料集](../../設定資料/README.md) · [取込対応表](../../設定資料/編集管理/取込対応表.md)

ユーザーから提供されたNotionエクスポートZIPの内容を、ファイル名・ディレクトリ構造・バイト列を変えずに `raw/` へ保存した。ZIP本体はDownloadsの提供元に残し、複製せずSHA-256を記録している。

- 元ZIP：`3d50892e-281c-428d-8ee4-3b8f18aaaa51_ExportBlock-8f3e3c9f-1acb-473a-b298-6728b076bee4.zip`
- 取込日：2026-09-07
- ファイル数：107（画像4点を含む）
- ZIP SHA-256：`d8e2435c7cfbd64fc4f69eb6df76953e01e9b0c9d3e4a11b2e32a8fd02865c5c`

## 保存内容

- [原文入口](raw/%E3%83%AA%E3%83%AA%E3%82%A2%E3%83%BC%E3%83%8A%E3%81%AE%E9%AD%94%E8%A1%93%E5%B8%AB%E8%87%AA%E5%8F%99%E4%BC%9D%2006e55439e54149cbbd22615891f1f85a.md)
- [manifest.json](manifest.json)：元ZIPと展開ファイルのハッシュ・サイズ。
- [coverage.json](coverage.json)：各原ファイルの整理先・保存理由。
- [catalog.json](catalog.json)：元の項目名と整理版パス。
- [view-conflicts.json](view-conflicts.json)：主要人物の全件CSVと個別プロフィールCSVで競合した非空欄値（今回0件）。
- [検証記録](verification.md)：原文一致、リンク、収録内容の検証結果。

## 原文と整理版

`raw/` は原文の保存場所。設定を編集する際は `設定資料/` の整理版を使う。Notion原文には、今回のZIPに含まれないリンク先があるため、その欠落を原文の改変で埋めていない。

`tools/organize.py` は今回の初回整形処理の記録。索引や編集上の要約は別途作成しており、資料集全体を再生成するツールではない。既存の整理記事がある場合は上書きせず停止する。
