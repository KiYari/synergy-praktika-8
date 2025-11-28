[app]
title = Notes App
package.name = notesapp
package.domain = org.example

source.dir = .
source.main = main.py

version = 1.0
version.regex = __version__ = ['"](.*)['"]
version.filename = %(source.dir)s/main.py

requirements = python3,kivy,kivymd,sqlite3

android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.sdk = 23
android.ndk = 25b

orientation = portrait

android.arch = arm64-v8a, armeabi-v7a

fullscreen = 0
log_level = 2

# Уровень логирования
log_level = 2