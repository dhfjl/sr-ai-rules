#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 v2fly/domain-list-community 的上游域名列表编译成 Shadowrocket 可用的规则集(.list)。

- 递归展开 include:xxx，自动去重
- 普通域名 -> DOMAIN-SUFFIX，full: -> DOMAIN，keyword: -> DOMAIN-KEYWORD
- regexp: 在 Shadowrocket 中没有对应规则类型，跳过并告警
- 默认排除带 @cn 属性的条目（国内可直连，应交给直连规则），--keep-cn 可保留
- 仅使用标准库，GitHub Actions 无需安装依赖

用法示例：
  python3 scripts/generate_rules.py
  python3 scripts/generate_rules.py --keep-cn
  python3 scripts/generate_rules.py --root openai --out dist/openai.list
"""
import argparse
import re
import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/{}"
TIMEOUT = 30
MAX_INCLUDE_DEPTH = 16
TYPE_MAP = {"": "DOMAIN-SUFFIX", "full": "DOMAIN", "keyword": "DOMAIN-KEYWORD"}
ENTRY_RE = re.compile(r"^(full|keyword|regexp):(.+)$")
HEADER = "# Auto-generated from v2fly/domain-list-community. Do not edit by hand."

_cache = {}


def fetch(name):
    if name not in _cache:
        req = urllib.request.Request(
            BASE_URL.format(name), headers={"User-Agent": "sr-rule-builder/1.0"}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            _cache[name] = resp.read().decode("utf-8")
    return _cache[name]


def walk(name, keep_cn, rules, seen, stats, depth=0):
    if name in seen:
        return
    seen.add(name)
    if depth > MAX_INCLUDE_DEPTH:
        stats["too_deep"] += 1
        return
    try:
        text = fetch(name)
    except Exception as exc:  # 上游偶发坏 include / 网络抖动：告警后继续
        stats["fetch_failed"] += 1
        print("[warn] 拉取失败 %s: %s" % (name, exc), file=sys.stderr)
        return
    stats["files"] += 1
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        tokens = line.split()
        entry = tokens[0]
        attrs = {t[1:] for t in tokens[1:] if t.startswith("@")}
        if entry.startswith("include:"):
            walk(entry[len("include:"):].strip(), keep_cn, rules, seen, stats, depth + 1)
            continue
        if not keep_cn and "cn" in attrs:
            stats["cn_excluded"] += 1
            continue
        m = ENTRY_RE.match(entry)
        prefix, value = (m.group(1), m.group(2)) if m else ("", entry)
        if prefix == "regexp":
            stats["regexp_skipped"] += 1
            print("[warn] 跳过无法映射的 regexp 条目: %s" % entry, file=sys.stderr)
            continue
        value = value.strip().lower().rstrip(".")
        if not value:
            continue
        rules[(TYPE_MAP[prefix], value)] = True


def main():
    ap = argparse.ArgumentParser(description="v2fly 域名列表 -> Shadowrocket 规则集")
    ap.add_argument("--root", default="category-ai-!cn", help="上游列表名（data/ 下的文件名）")
    ap.add_argument("--out", default=None, help="输出路径，默认 dist/<root>.list")
    ap.add_argument("--keep-cn", action="store_true", help="保留带 @cn 属性的条目（默认排除）")
    args = ap.parse_args()

    out_path = Path(args.out) if args.out else Path("dist") / (args.root + ".list")
    stats = {"files": 0, "fetch_failed": 0, "too_deep": 0, "cn_excluded": 0, "regexp_skipped": 0}
    rules = {}
    walk(args.root, args.keep_cn, rules, set(), stats)
    if not rules:
        print("[error] 没有生成任何规则，上游可能不可达", file=sys.stderr)
        return 1

    order = ["DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"]
    keys = sorted(rules, key=lambda k: (order.index(k[0]), k[1]))
    lines = [HEADER] + ["%s,%s" % k for k in keys]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("上游文件 %d 个 | 生成规则 %d 条 -> %s" % (stats["files"], len(lines) - 1, out_path))
    print("排除 @cn %d 条 | 跳过 regexp %d 条 | 拉取失败 %d 个文件"
          % (stats["cn_excluded"], stats["regexp_skipped"], stats["fetch_failed"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
