# Unityプロジェクトを GitHub に移す手順（家のパソコン・Windows）

1. GitHub で、非公開（Private）のリポジトリ `dot-meikyu-unity` を作る。
2. GitHub Desktop で、そのリポジトリを取ってくる（File > Clone repository）。
3. 取ってきたフォルダの中に、Unityのプロジェクトのフォルダの中身（`Assets`、`Packages`、`ProjectSettings` など）をコピーする。
   - `Library`、`Temp`、`Logs`、`obj` は入れない（入れても `.gitignore` が除く）。
4. この `.gitignore` を、そのいちばん上のフォルダに置く。
5. GitHub Desktop に、変更の一覧が出る。左下に「最初のプロジェクト」と書いて、**Commit to main** → **Push origin**。
6. 100MBをこえる大きいファイルがあると、送れない。そのときは、Git LFS を使う（私に言ってください）。

注意：`*.keystore`（アプリの署名の鍵）は、絶対に送らない。なくすと、アプリの更新ができなくなるので、別の場所（USBなど）にも保管する。
