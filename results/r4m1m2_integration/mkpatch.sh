#!/bin/bash
# usage: mkpatch.sh <olddir> <newdir> <out>; paper-relative paths a/ b/
set -e; old=$1; new=$2; out=$3; : > "$out"
for f in manuscript.tex Supplementary.tex sn-bibliography.bib "Response letter.tex"; do
  if ! cmp -s "$old/$f" "$new/$f"; then
    diff -u --label "a/$f	2026-11-16 00:00:00.000000000 +0000" --label "b/$f	2026-11-16 00:00:00.000000000 +0000" "$old/$f" "$new/$f" >> "$out" || true
  fi
done
