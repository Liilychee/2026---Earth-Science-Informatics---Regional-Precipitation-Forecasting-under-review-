#!/bin/bash
set -e; R=$1; for tool in git bsd; do
  W=$(mktemp -d); cp -p "$R"/before/* "$W"/; cd "$W"
  for p in R4_M1_LABELFIX_LOCAL R4_M2_LOCAL; do
    if [ $tool = git ]; then git apply -p1 "$OLDPWD/$R/$p.patch"; else /usr/bin/patch -s -p1 < "$OLDPWD/$R/$p.patch"; fi
  done
  cd "$OLDPWD"; for f in manuscript.tex Supplementary.tex sn-bibliography.bib "Response letter.tex"; do cmp "$W/$f" "$R/after/$f" && echo "$tool $f identical"; done; rm -rf "$W"
done
