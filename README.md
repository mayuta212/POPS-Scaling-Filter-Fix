# POPS Scaling Filter Fix

PSPのPS1エミュレーター（POPS）の**AV出力ケーブルのぼけを改善**するプラグインです。純正の拡大率・表示比率は変更しません。

**対象環境:** PSP-3000 (04g) / 6.61 / ARK-5
![OFF / FILTER FIX](images/ChatGPT%20%E7%94%BB%E5%83%8F%202026%E5%B9%B410%E6%9C%8828%E6%97%A5%2005_49_22.png)

| PS1の水平解像度 | フィルター |
| --- | --- |
| 256・320・640 | **Nearest（くっきり）** |
| 368系・512 | Linear |

ゲーム中の解像度変更にも、対応する描画経路では自動追従します。すべてのゲームでの動作を保証するものではありません。

## ダウンロード・導入

[Releases](https://github.com/mayuta212/POPS-Scaling-Filter-Fix/releases) から `PopsScaleFilter.prx` を取得し、PSPのPOPS用プラグインとして有効化してください。以前の `PopsTVUnlock.prx` とは併用しないでください。交換時はPOPSを完全終了してください。

## Build (PSPDEV)

```sh
make clean && make
```

出力ファイル：`PopsScaleFilter.prx`。対応外のPOPSテキストではパッチを適用しません。実行時のログ採取はありません。Sonyのファームウェアバイナリは含みません。

MIT License.
