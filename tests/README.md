# オフライン検証（任意）

実機から自身で取得した `POPS_TV_DUMP.zip` を手元に用意し、リポジトリのルートで実行：

```sh
python3 tests/verify_offline.py /path/to/POPS_TV_DUMP.zip
python3 tests/verify_relocation.py /path/to/POPS_TV_DUMP.zip
python3 tests/verify_guard_regression.py
```

Sonyの `POPS.BIN` は収録・再配布していません。 `stub.S` は機械語照合用でPRXのリンク対象外です。PSP実機での互換性を保証するテストではありません。
