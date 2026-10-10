#!/usr/bin/env python3
"""Join DLsite platform genre/tag codes with the frozen TOL census and
classify each code for font-niche relevance.

DLsite's "platform-chosen tags" are a shared genre/tag system: creators select
tags during work registration, and every tag renders on product pages as a
clickable search link carrying a stable 3-digit code (e.g. /genre/016).

Sources:
- Code->label map: outputs/research/dlsite-platform-tag-bank/source-genre-codes-hirokotb-2024-06.csv
  (third-party observation of 2024-06-15, codes 001-635).
- Census usage: outputs/research/dlsite-live-collector/dlsite.db (frozen
  snapshot 2026-09-09, 1,629 Tools/Accessories items; item_genres covers the
  220 products whose detail Genre row was fetched).

Output: outputs/research/dlsite-platform-tag-bank.csv

Levels:
- A-DIRECT-FONT   : tag actually attached to a census font product (all-ages selectable).
- R18-FONT-ONLY   : tag attached to census fonts that are R18 doujin-content fonts.
- B-ADJACENT-TOOL : creator-tool / asset-shelf tag observed in the TOL census.
- C-WORLD-STYLE   : all-ages worldbuilding/style tag plausibly usable for a
                    display font, even where unobserved in the census.
- D-TECHNICAL     : technical/descriptor tags relevant to installing or
                    marketing a font/tool product.
- X-EXCLUDE-ADULT : adult-only/body/relationship tags (irrelevant to all-ages fonts).
- X-EXCLUDE-OTHER : tags observed in the shelf but not usable for fonts.
- REVIEW          : observed or relevant code that needs a human decision.

Catalog counts are coverage signals only, never demand or sales.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_CSV = ROOT / "outputs/research/dlsite-platform-tag-bank/source-genre-codes-hirokotb-2024-06.csv"
DB = ROOT / "outputs/research/dlsite-live-collector/dlsite.db"
OUT_CSV = ROOT / "outputs/research/dlsite-platform-tag-bank.csv"

# code -> (level, note). Codes omitted default to X-EXCLUDE-OTHER (or REVIEW if
# observed in the census and left unclassified here).
CURATION: dict[str, tuple[str, str]] = {
    # --- A-DIRECT-FONT: observed on census font products, all-ages selectable ---
    "016": ("A-DIRECT-FONT", "ファンタジー on RJ152049 Granaria (57 DL); all-ages; worldbuilding display fonts"),
    "053": ("A-DIRECT-FONT", "健全 (General/all-ages) on RJ110793 妄想○ーンカタカナ; safe catch-all for all-ages fonts"),
    "507": ("A-DIRECT-FONT", "技術書 on RJ01479594 ぱぱっと!イメージツリー; creator-tool book audience"),
    "508": ("A-DIRECT-FONT", "TRPG on RJ01479594; TRPG scenario/title-lettering fonts"),
    "516": ("A-DIRECT-FONT", "TRPGシナリオ on RJ01479594; TRPG material shelf"),
    "510": ("A-DIRECT-FONT", "ツクール on RJ01479594; RPG Maker asset audience (title screens, UI)"),
    "073": ("A-DIRECT-FONT", "アニメ on RJ01479594; anime/illustration creator audience"),

    # --- R18-FONT-ONLY: attached to R18 doujin-content fonts in the census ---
    "066": ("R18-FONT-ONLY", "マニアック/変態 on 豊国文字 RJ096283 and 妄想カタカナ RJ110793; only for R18/explicit-content fonts"),

    # --- B-ADJACENT-TOOL: creator-tool / asset-tool tags observed in TOL census ---
    "509": ("B-ADJACENT-TOOL", "3D作品 160 TOL items; 3D asset/maker audience"),
    "296": ("B-ADJACENT-TOOL", "シリーズもの 68 items; series/multi-weight positioning"),
    "312": ("B-ADJACENT-TOOL", "きせかえ 13 items; dress-up/game asset audience"),
    "588": ("B-ADJACENT-TOOL", "素材集 2 TOL items; material/asset bundle shelf (REJECTED as freeform keyword; distinct surface here)"),
    "431": ("B-ADJACENT-TOOL", "ドット 3 items; pixel-art maker audience"),
    "512": ("B-ADJACENT-TOOL", "東方Project 3 items; Touhou fan-game asset audience"),
    "513": ("B-ADJACENT-TOOL", "VTuber (unobserved in census but high-fit for FontFairy thumbnail/VTuber lettering fonts)"),

    # --- C-WORLD-STYLE: all-ages worldbuilding/style tags usable for display fonts ---
    "010": ("C-WORLD-STYLE", "SF; sci-fi title fonts"),
    "013": ("C-WORLD-STYLE", "ほのぼの; soft/cute rounded fonts"),
    "017": ("C-WORLD-STYLE", "歴史/時代物; historical/old-style display fonts"),
    "019": ("C-WORLD-STYLE", "ホラー (all-ages ok); horror lettering"),
    "026": ("C-WORLD-STYLE", "オカルト; occult/mystic lettering"),
    "029": ("C-WORLD-STYLE", "魔法; magic/fantasy-lettering descriptor"),
    "235": ("C-WORLD-STYLE", "エルフ/妖精; fantasy-style fonts"),
    "240": ("C-WORLD-STYLE", "魔法少女; cute/magical lettering"),
    "243": ("C-WORLD-STYLE", "妖怪; yokai/japanese-folklore fonts"),
    "254": ("C-WORLD-STYLE", "ロボット/アンドロイド; mecha/tech lettering"),
    "414": ("C-WORLD-STYLE", "ゾンビ (all-ages ok); horror/zombie title fonts"),
    "519": ("C-WORLD-STYLE", "異世界転生; isekai light-novel/title fonts"),
    "520": ("C-WORLD-STYLE", "悪役令嬢; villainess LN display fonts"),
    "541": ("C-WORLD-STYLE", "獣人; kemono/fantasy-race lettering"),

    # --- D-TECHNICAL: descriptor tags for a font/tool product ---
    "623": ("D-TECHNICAL", "パソコン/OS/ハードウェア; installability context"),
    "624": ("D-TECHNICAL", "言語/プログラミング; programming/tech audience"),
    "625": ("D-TECHNICAL", "デザイン/グラフィックス; direct design-tool descriptor"),
    "626": ("D-TECHNICAL", "海外/翻訳; international/translation fonts"),

    # --- X-EXCLUDE-ADULT --- (many; representative + bulky ones explicitly recorded)
    "049": ("X-EXCLUDE-ADULT", "着衣 adult fetish tag"),
    "062": ("X-EXCLUDE-ADULT", "脚 body tag"),
    "063": ("X-EXCLUDE-ADULT", "お尻/ヒップ body tag"),
    "065": ("X-EXCLUDE-ADULT", "おっぱい body tag"),
    "074": ("X-EXCLUDE-ADULT", "制服 costume/adult tag"),
    "075": ("X-EXCLUDE-ADULT", "セーラー服 costume/adult tag"),
    "078": ("X-EXCLUDE-ADULT", "メイド costume/adult tag"),
    "080": ("X-EXCLUDE-OTHER", "巫女 costume image tag; not font-relevant"),
    "082": ("X-EXCLUDE-ADULT", "下着 adult tag"),
    "112": ("X-EXCLUDE-ADULT", "ノーマルプレイ and 100-series scenario tags: adult-only"),
    "113": ("X-EXCLUDE-ADULT", "adult-only scenario tags: never for all-ages fonts"),
    "491": ("X-EXCLUDE-ADULT", "女性向け; not a font descriptor"),

    # --- X-EXCLUDE-OTHER ---
    "001": ("X-EXCLUDE-OTHER", "学校/学園 mode tag; not a font descriptor"),
    "002": ("X-EXCLUDE-OTHER", "オフィス/職場 mode tag"),
    "003": ("X-EXCLUDE-OTHER", "屋外 mode tag"),
    "004": ("X-EXCLUDE-OTHER", "ラブラブ/あまあま mode tag"),
    "005": ("X-EXCLUDE-OTHER", "ギャグ mode tag; only for gag-specific products"),
    "006": ("X-EXCLUDE-OTHER", "退廃/背徳/インモラル adult-leaning tag"),
    "007": ("X-EXCLUDE-OTHER", "コメディ mode tag; only for comedy-specific products"),
    "008": ("X-EXCLUDE-OTHER", "日常/生活 mode tag"),
    "009": ("X-EXCLUDE-OTHER", "ミリタリー mode tag; niche war-games only"),
    "011": ("X-EXCLUDE-OTHER", "スポーツ mode tag"),
    "012": ("X-EXCLUDE-OTHER", "格闘 mode tag"),
    "014": ("X-EXCLUDE-OTHER", "恋人同士 mode tag"),
    "015": ("X-EXCLUDE-OTHER", "シリアス mode tag; product-tone, not font"),
    "018": ("X-EXCLUDE-OTHER", "【現在利用せず】 unused code"),
    "020": ("X-EXCLUDE-OTHER", "キャットファイト mode tag"),
    "022": ("X-EXCLUDE-OTHER", "サスペンス mode tag"),
    "024": ("X-EXCLUDE-OTHER", "バイオレンス mode tag"),
    "028": ("X-EXCLUDE-OTHER", "歳の差 mode tag"),
    "031": ("X-EXCLUDE-OTHER", "同居 mode tag"),
    "032": ("X-EXCLUDE-OTHER", "純愛 mode tag"),
    "033": ("X-EXCLUDE-OTHER", "耽美 adult-leaning tag"),
    "034": ("X-EXCLUDE-OTHER", "戦場 mode tag"),
    "037": ("X-EXCLUDE-OTHER", "ボーイズラブ floor-specific tag"),
    "051": ("X-EXCLUDE-OTHER", "萌え mode tag"),
    "052": ("X-EXCLUDE-OTHER", "燃え mode tag"),
    "055": ("X-EXCLUDE-OTHER", "感動 mode tag"),
    "056": ("X-EXCLUDE-OTHER", "癒し mode tag; ASMR/voice audiences"),
    "057": ("X-EXCLUDE-OTHER", "淡白/あっさり mode tag"),
    "058": ("X-EXCLUDE-OTHER", "オールハッピー mode tag"),
    "059": ("X-EXCLUDE-OTHER", "ツンデレ character tag"),
    "060": ("X-EXCLUDE-OTHER", "女性視点 POV tag"),
    "064": ("X-EXCLUDE-OTHER", "フェチ fetish tag"),
    "085": ("X-EXCLUDE-OTHER", "ゴスロリ costume tag"),
    "086": ("X-EXCLUDE-OTHER", "コスプレ costume tag"),
    "091": ("X-EXCLUDE-OTHER", "着物/和服 costume tag"),
    "111": ("X-EXCLUDE-OTHER", "女装 character tag"),
    "118": ("X-EXCLUDE-OTHER", "レズ/女同士 adult tag"),
    "119": ("X-EXCLUDE-OTHER", "ゲイ/男同士 adult tag"),
    "120": ("X-EXCLUDE-OTHER", "近親相姦/近親もの adult tag"),
    "137": ("X-EXCLUDE-OTHER", "緊縛 adult tag"),
    "142": ("X-EXCLUDE-OTHER", "淫乱 adult tag"),
    "143": ("X-EXCLUDE-OTHER", "露出 adult tag"),
    "146": ("X-EXCLUDE-OTHER", "拘束 adult tag"),
    "148": ("X-EXCLUDE-OTHER", "浣腸/下僕 adult tag"),
    "154": ("X-EXCLUDE-OTHER", "鬼畜 adult tag"),
    "157": ("X-EXCLUDE-OTHER", "催眠/トランス/暗示 adult tag (RBK notes トランス/暗示 observed)"),
    "158": ("X-EXCLUDE-OTHER", "百合 mode tag"),
    "171": ("X-EXCLUDE-OTHER", "黒髪 character/body attribute tag"),
    "175": ("X-EXCLUDE-OTHER", "ネコミミ character attribute tag"),
    "182": ("X-EXCLUDE-ADULT", "巨乳/爆乳 body tag"),
    "183": ("X-EXCLUDE-ADULT", "貧乳/微乳 body tag"),
    "196": ("X-EXCLUDE-OTHER", "方言 voice/dialect tag"),
    "197": ("X-EXCLUDE-OTHER", "ボクっ娘 character tag"),
    "198": ("X-EXCLUDE-OTHER", "無表情 character tag"),
    "206": ("X-EXCLUDE-OTHER", "少女 character tag"),
    "207": ("X-EXCLUDE-OTHER", "ロリ character tag"),
    "208": ("X-EXCLUDE-OTHER", "ぷに body/character tag"),
    "209": ("X-EXCLUDE-OTHER", "年上 character tag"),
    "210": ("X-EXCLUDE-OTHER", "少年 character tag"),
    "211": ("X-EXCLUDE-OTHER", "ショタ character tag"),
    "212": ("X-EXCLUDE-OTHER", "妹 character tag"),
    "218": ("X-EXCLUDE-OTHER", "熟女 character tag"),
    "219": ("X-EXCLUDE-OTHER", "人妻 character tag"),
    "220": ("X-EXCLUDE-OTHER", "お姉さん character tag"),
    "222": ("X-EXCLUDE-OTHER", "幼なじみ character tag"),
    "223": ("X-EXCLUDE-OTHER", "双子 character tag"),
    "226": ("X-EXCLUDE-OTHER", "女教師 character tag"),
    "230": ("X-EXCLUDE-OTHER", "サラリーマン character tag"),
    "232": ("X-EXCLUDE-OTHER", "OL character tag"),
    "233": ("X-EXCLUDE-OTHER", "戦士 character tag"),
    "234": ("X-EXCLUDE-OTHER", "女王様/お姫様 character tag"),
    "237": ("X-EXCLUDE-OTHER", "天使/悪魔 character tag"),
    "242": ("X-EXCLUDE-OTHER", "お嬢様 character tag"),
    "244": ("X-EXCLUDE-OTHER", "ニューハーフ character tag"),
    "245": ("X-EXCLUDE-OTHER", "性転換(TS) character tag"),
    "246": ("X-EXCLUDE-OTHER", "天然 character tag"),
    "249": ("X-EXCLUDE-OTHER", "擬人化 character tag"),
    "250": ("X-EXCLUDE-OTHER", "女体化 character tag"),
    "251": ("X-EXCLUDE-OTHER", "けもの/獣化 character tag"),
    "255": ("X-EXCLUDE-OTHER", "メガネ character tag"),
    "268": ("X-EXCLUDE-OTHER", "姉妹 character tag"),
    "274": ("X-EXCLUDE-OTHER", "兄 character tag"),
    "275": ("X-EXCLUDE-OTHER", "弟 character tag"),
    "276": ("X-EXCLUDE-OTHER", "父 character tag"),
    "281": ("X-EXCLUDE-OTHER", "同級生/同僚 character tag"),
    "285": ("X-EXCLUDE-OTHER", "先輩/後輩 character tag"),
    "293": ("X-EXCLUDE-OTHER", "執事 character tag"),
    "298": ("X-EXCLUDE-OTHER", "ミステリー mode tag"),
    "303": ("X-EXCLUDE-OTHER", "男の娘 character tag"),
    "308": ("X-EXCLUDE-OTHER", "料理/グルメ content tag"),
    "309": ("X-EXCLUDE-OTHER", "アンソロジー collection tag"),
    "310": ("X-EXCLUDE-OTHER", "評論 critical-writing tag"),
    "311": ("X-EXCLUDE-ADULT", "おさわり adult tag"),
    "314": ("X-EXCLUDE-OTHER", "催眠音声 adult voice tag"),
    "316": ("X-EXCLUDE-OTHER", "ヤンデレ character tag"),
    "317": ("X-EXCLUDE-OTHER", "人外娘/モンスター娘 character tag"),
    "318": ("X-EXCLUDE-OTHER", "社長 character tag"),
    "319": ("X-EXCLUDE-OTHER", "医者 character tag"),
    "321": ("X-EXCLUDE-OTHER", "褐色/日焼け body tag"),
    "327": ("X-EXCLUDE-OTHER", "レディースコミック floor tag"),
    "399": ("X-EXCLUDE-OTHER", "青年 manga-audience tag"),
    "400": ("X-EXCLUDE-OTHER", "学生 character tag"),
    "401": ("X-EXCLUDE-OTHER", "ガテン系 character tag"),
    "405": ("X-EXCLUDE-OTHER", "レスラー/格闘家 character tag"),
    "409": ("X-EXCLUDE-OTHER", "芸能人/アイドル/モデル character tag"),
    "411": ("X-EXCLUDE-OTHER", "体育会系/スポーツ選手 character tag"),
    "412": ("X-EXCLUDE-OTHER", "外国人 character tag"),
    "419": ("X-EXCLUDE-OTHER", "不良/ヤンキー character tag"),
    "422": ("X-EXCLUDE-OTHER", "俺様 character tag"),
    "442": ("X-EXCLUDE-OTHER", "耳かき ASMR/voice tag"),
    "454": ("X-EXCLUDE-OTHER", "動物/ペット content tag"),
    "455": ("X-EXCLUDE-OTHER", "ラブコメ mode tag"),
    "472": ("X-EXCLUDE-OTHER", "ガチムチ body tag"),
    "478": ("X-EXCLUDE-OTHER", "短髪 body tag"),
    "484": ("X-EXCLUDE-OTHER", "腹パン gimmick tag"),
    "491": ("X-EXCLUDE-OTHER", "女性向け floor tag"),
    "492": ("X-EXCLUDE-OTHER", "英語作品 English-work tag; useful for EN font products"),
    "494": ("X-EXCLUDE-OTHER", "ロマンス mode tag"),
    "496": ("X-EXCLUDE-OTHER", "バイノーラル/ダミヘ voice/ASMR tag"),
    "497": ("X-EXCLUDE-OTHER", "ASMR voice tag"),
    "498": ("X-EXCLUDE-OTHER", "DLsite翻訳作品 translation tag"),
    "502": ("X-EXCLUDE-OTHER", "男主人公 POV tag"),
    "503": ("X-EXCLUDE-OTHER", "ささやき voice tag"),
    "504": ("X-EXCLUDE-OTHER", "おねショタ character tag"),
    "505": ("X-EXCLUDE-OTHER", "くノ一 character tag"),
    "506": ("X-EXCLUDE-OTHER", "サキュバス/淫魔 adult tag"),
    "511": ("X-EXCLUDE-OTHER", "ライトノベル LN tag; relevant for LN title fonts"),
    "514": ("X-EXCLUDE-OTHER", "オナサポ adult tag"),
    "515": ("X-EXCLUDE-OTHER", "総集編 anthology tag"),
    "517": ("X-EXCLUDE-OTHER", "TRPGリプレイ集 TRPG variant"),
    "518": ("X-EXCLUDE-OTHER", "TRPGルールブック TRPG variant"),
    "542": ("X-EXCLUDE-OTHER", "文芸 literature tag"),
    "543": ("X-EXCLUDE-OTHER", "文芸その他 literature tag"),
    "544": ("X-EXCLUDE-OTHER", "冒険/戦記 literature tag"),
    "545": ("X-EXCLUDE-OTHER", "新文芸 literature tag"),
    "546": ("X-EXCLUDE-OTHER", "レディース文庫 literature tag"),
    "547": ("X-EXCLUDE-OTHER", "文学 literature tag"),
    "548": ("X-EXCLUDE-OTHER", "伝奇小説 literature tag"),
    "549": ("X-EXCLUDE-OTHER", "経済/社会小説 literature tag"),
    "550": ("X-EXCLUDE-OTHER", "エッセイ/紀行 literature tag"),
    "551": ("X-EXCLUDE-OTHER", "メディア化 meta tag"),
    "552": ("X-EXCLUDE-OTHER", "エンターテイメント broad tag"),
    "553": ("X-EXCLUDE-OTHER", "雑学/サブカルチャー broad tag"),
    "554": ("X-EXCLUDE-OTHER", "復刻版 reprint tag"),
    "555": ("X-EXCLUDE-OTHER", "教養一般 broad tag"),
    "556": ("X-EXCLUDE-OTHER", "哲学/思想/精神世界 broad tag"),
    "557": ("X-EXCLUDE-OTHER", "タレント/アイドル broad tag"),
    "558": ("X-EXCLUDE-OTHER", "情報系/情報誌 magazine tag"),
    "559": ("X-EXCLUDE-OTHER", "一般 broad magazine tag"),
    "560": ("X-EXCLUDE-OTHER", "風景/動物 photography tag"),
    "561": ("X-EXCLUDE-OTHER", "グラビア/ヌード adult photo tag"),
    "562": ("X-EXCLUDE-OTHER", "ボーイズ photo tag"),
    "563": ("X-EXCLUDE-OTHER", "イラスト集 illustration-collection tag"),
    "564": ("X-EXCLUDE-OTHER", "AI写真集 AI photo tag"),
    "565": ("X-EXCLUDE-OTHER", "人文/社会科学 academic tag"),
    "566": ("X-EXCLUDE-OTHER", "心理学 academic tag"),
    "567": ("X-EXCLUDE-OTHER", "教育一般 academic tag"),
    "568": ("X-EXCLUDE-OTHER", "芸術/美術一般 academic tag"),
    "569": ("X-EXCLUDE-OTHER", "写真一般 photography tag"),
    "570": ("X-EXCLUDE-OTHER", "画集 art-book tag"),
    "571": ("X-EXCLUDE-OTHER", "音楽/楽譜 music tag"),
    "576": ("X-EXCLUDE-OTHER", "ゲーム攻略本 guide tag"),
    "577": ("X-EXCLUDE-OTHER", "趣味/実用一般 hobby tag"),
    "579": ("X-EXCLUDE-OTHER", "釣り/登山/アウトドア hobby tag"),
    "580": ("X-EXCLUDE-OTHER", "鉄道 hobby tag"),
    "581": ("X-EXCLUDE-OTHER", "車/バイク hobby tag"),
    "583": ("X-EXCLUDE-OTHER", "占い hobby tag"),
    "584": ("X-EXCLUDE-OTHER", "クイズ/パズル hobby tag"),
    "585": ("X-EXCLUDE-OTHER", "華道/茶道/香道 hobby tag"),
    "586": ("X-EXCLUDE-OTHER", "囲碁/将棋 hobby tag"),
    "587": ("X-EXCLUDE-OTHER", "競馬/パチンコ/ギャンブル hobby tag"),
    "589": ("X-EXCLUDE-OTHER", "模型/プラモデル hobby tag"),
    "590": ("X-EXCLUDE-OTHER", "まんが読み物/コミックエッセイ manga tag"),
    "591": ("X-EXCLUDE-OTHER", "園芸 hobby tag"),
    "592": ("X-EXCLUDE-OTHER", "ゲーム/eスポーツ game tag"),
    "593": ("X-EXCLUDE-OTHER", "暮らし/健康/子育て lifestyle tag"),
    "595": ("X-EXCLUDE-OTHER", "家事/マナー lifestyle tag"),
    "596": ("X-EXCLUDE-OTHER", "ファッション lifestyle tag"),
    "597": ("X-EXCLUDE-OTHER", "旅行/地理/ガイド lifestyle tag"),
    "598": ("X-EXCLUDE-OTHER", "資格/検定/就職 education tag"),
    "599": ("X-EXCLUDE-OTHER", "語学 language tag; EN-font adjacent"),
    "600": ("X-EXCLUDE-OTHER", "参考書/問題集 education tag"),
    "601": ("X-EXCLUDE-OTHER", "小学学参 education tag"),
    "602": ("X-EXCLUDE-OTHER", "中学学参 education tag"),
    "603": ("X-EXCLUDE-OTHER", "高校学参 education tag"),
    "604": ("X-EXCLUDE-OTHER", "辞典 reference tag"),
    "605": ("X-EXCLUDE-OTHER", "社会/政治 academic tag"),
    "606": ("X-EXCLUDE-OTHER", "法律 academic tag"),
    "607": ("X-EXCLUDE-OTHER", "ビジネス/経済 academic tag"),
    "608": ("X-EXCLUDE-OTHER", "経営/経営学 academic tag"),
    "609": ("X-EXCLUDE-OTHER", "マーケティング academic tag"),
    "610": ("X-EXCLUDE-OTHER", "会計/簿記 academic tag"),
    "611": ("X-EXCLUDE-OTHER", "ビジネス一般 academic tag"),
    "612": ("X-EXCLUDE-OTHER", "自己啓発 academic tag"),
    "613": ("X-EXCLUDE-OTHER", "企業法務 academic tag"),
    "614": ("X-EXCLUDE-OTHER", "開業/転職/就職 academic tag"),
    "615": ("X-EXCLUDE-OTHER", "広告/セールス academic tag"),
    "616": ("X-EXCLUDE-OTHER", "仕事の技術 academic tag"),
    "617": ("X-EXCLUDE-OTHER", "流通 academic tag"),
    "618": ("X-EXCLUDE-OTHER", "ビジネス資格試験 academic tag"),
    "619": ("X-EXCLUDE-OTHER", "IT/Eビジネス academic tag"),
    "620": ("X-EXCLUDE-OTHER", "資産運用 academic tag"),
    "621": ("X-EXCLUDE-OTHER", "理学/科学 academic tag"),
    "622": ("X-EXCLUDE-OTHER", "工学一般 academic tag"),
    "627": ("X-EXCLUDE-OTHER", "医学 academic tag"),
    "628": ("X-EXCLUDE-OTHER", "看護学 academic tag"),
    "629": ("X-EXCLUDE-OTHER", "薬学 academic tag"),
    "630": ("X-EXCLUDE-OTHER", "日記手帳 lifestyle tag"),
    "631": ("X-EXCLUDE-OTHER", "雑誌/ムック/その他 magazine tag"),
    "632": ("X-EXCLUDE-OTHER", "女性向け総合(雑誌) magazine tag"),
    "633": ("X-EXCLUDE-OTHER", "男性向け総合(雑誌) magazine tag"),
    "634": ("X-EXCLUDE-OTHER", "オーディオブック audio tag"),
    "635": ("X-EXCLUDE-OTHER", "【未利用】 unused code"),
}

LEVEL_ORDER = ["A-DIRECT-FONT", "R18-FONT-ONLY", "B-ADJACENT-TOOL",
               "C-WORLD-STYLE", "D-TECHNICAL", "REVIEW",
               "X-EXCLUDE-ADULT", "X-EXCLUDE-OTHER"]


def load_codes():
    codes = {}
    with open(SOURCE_CSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            code = row["番号"].strip()
            old = (row["旧ジャンル"] or "").strip()
            cur = (row["現行ジャンル"] or "").strip()
            diff = (row["差分がある場合"] or "").strip()
            codes[code] = {"code": code, "old": old, "current": cur, "diff": diff}
    return codes


def label_variants(entry):
    labels = [entry["old"], entry["current"], entry["diff"]]
    out = set()
    for lab in labels:
        if not lab or lab in ("【現在利用せず】", "【未利用】"):
            continue
        out.add(lab)
        for part in re_split(lab):
            out.add(part)
    return out


def re_split(label):
    import re
    return [p for p in re.split(r"[/／,、・\s]+", label) if p]


START_CHAR = {str(n): set() for n in range(1, 636)}


def match_census(codes, con):
    """Return code -> {items, font_items, font_products} matched by label."""
    stats = {code: {"items": set(), "fonts": set()} for code in codes}
    cur = con.cursor()
    cur.execute("""
        SELECT ig.product_id, ig.genre, i.is_font
        FROM item_genres ig JOIN items i ON i.product_id = ig.product_id
    """)
    unmatched = {}
    for pid, genre, is_font in cur.fetchall():
        matched = False
        for code, entry in codes.items():
            if genre in label_variants(entry):
                stats[code]["items"].add(pid)
                if is_font:
                    stats[code]["fonts"].add(pid)
                matched = True
        if not matched:
            unmatched.setdefault(genre, set()).add(pid)
    return stats, unmatched


def main():
    codes = load_codes()
    con = sqlite3.connect(DB)
    stats, unmatched = match_census(codes, con)

    # font product id -> title for annotations
    font_titles = dict(con.execute(
        "SELECT product_id, title FROM v_fonts"))
    con.close()

    rows = []
    for code in sorted(codes, key=lambda c: int(c)):
        e = codes[code]
        s = stats[code]
        level, note = CURATION.get(code, (None, ""))
        if not level:
            if s["items"]:
                level, note = "REVIEW", "Observed in census; unclassified"
            else:
                level, note = "X-EXCLUDE-OTHER", "Not observed, not curated"
        rows.append({
            "code": code,
            "label": e["current"],
            "label_old": e["old"],
            "replaced_label": e["diff"],
            "status": "unused" if e["current"] in ("【現在利用せず】", "【未利用】") else "active",
            "census_items": len(s["items"]),
            "census_font_items": len(s["fonts"]),
            "font_products": " / ".join(sorted(font_titles[p][:40] for p in s["fonts"])),
            "level": level,
            "note": note,
        })

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT_CSV} ({len(rows)} codes)")
    print("\n=== Level counts ===")
    from collections import Counter
    for level, n in Counter(r["level"] for r in rows).most_common():
        print(f"  {level}: {n}")

    print("\n=== Relevant rows (A/B/C/D) ===")
    for r in rows:
        if r["level"].startswith(("A-", "B-", "C-", "D-")):
            print(f"  {r['code']} {r['label']:14s} census={r['census_items']:3d} fonts={r['census_font_items']} {r['level']}")

    print("\n=== REVIEW (observed but unclassified) ===")
    for r in rows:
        if r["level"] == "REVIEW":
            print(f"  {r['code']} {r['label']:14s} census={r['census_items']} fonts={r['census_font_items']}")

    print("\n=== UNMATCHED census labels ===")
    for genre, pids in sorted(unmatched.items()):
        print(f"  {genre!r} ({len(pids)} items): {', '.join(sorted(pids)[:8])}")


if __name__ == "__main__":
    main()