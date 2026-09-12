[app]
title = WalkLearn
package.name = walklearn
package.domain = org.walklearn
source.dir = .
source.include_exts = py,json,ttf,png
version = 1.0.0
requirements = python3,kivy,pyjnius,arabic-reshaper,python-bidi
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.api = 35
android.minapi = 23
android.ndk = 27c
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.backup_rules = 
