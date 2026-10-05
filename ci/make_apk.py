#!/usr/bin/env python3
"""把构建出的 libphira.so 替换进官方 APK，产出未签名的 APK。

用法: make_apk.py <官方.apk> <libphira.so> <abi> <输出.apk>

为什么需要它：
  TeamFlos/phira 仓库里没有 Android 前端工程（无 gradle / manifest / Java 源码），
  官方 APK 是唯一可用的宿主外壳。官方文档 phira-docs 的 Android.md 给的路子就是
  "手动替换 apk 下 libphira.so 文件"，本脚本把那一步自动化。

实现要点：
  只替换 lib/<abi>/libphira.so 一个条目，其余条目原样搬运（保留各自的压缩方式），
  这样 resources.arsc 仍然是 STORED、条目顺序不变。对齐与签名交给 zipalign /
  apksigner 在 CI 里完成（顺序必须是 align → sign，签名后再对齐会破坏签名）。
"""

import sys
import zipfile

SO_ENTRY = "lib/{abi}/libphira.so"


def main() -> None:
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    apk_in, so_path, abi, apk_out = sys.argv[1:5]

    entry = SO_ENTRY.format(abi=abi)
    with open(so_path, "rb") as f:
        so_data = f.read()

    replaced = False
    with zipfile.ZipFile(apk_in) as zin, zipfile.ZipFile(apk_out, "w") as zout:
        for item in zin.infolist():
            if item.filename == entry:
                data = so_data
                replaced = True
            else:
                data = zin.read(item.filename)
            info = zipfile.ZipInfo(item.filename, date_time=item.date_time)
            info.compress_type = item.compress_type
            info.external_attr = item.external_attr
            info.internal_attr = item.internal_attr
            info.create_system = item.create_system
            zout.writestr(info, data)

    if not replaced:
        sys.exit(f"错误: {apk_in} 中找不到 {entry}")
    print(f"{apk_out}: 已替换 {entry} -> {len(so_data):,} B")


if __name__ == "__main__":
    main()
