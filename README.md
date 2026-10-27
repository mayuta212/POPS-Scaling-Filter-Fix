# POPS Scaling Filter Fix

A PSP POPS plugin that adjusts **AV output** texture filtering without changing the original display scaling or aspect ratio.

| PS1 horizontal mode | Filter |
| --- | --- |
| 256 / 320 / 640 | **Nearest** |
| 368 / 512 | Linear |

The filter is reapplied along the supported rendering path after in-game resolution changes.

**Target:** PSP-3000 (04g), firmware 6.61, ARK-5. Other configurations are untested.

## Build

With PSPDEV installed, run `make clean && make` to generate **`PopsScaleFilter.prx`**. Install it as a POPS plugin; do not run it together with earlier `PopsTVUnlock.prx` versions. Fully exit and restart POPS when changing plugins.

This is source-only. No Sony firmware binaries are included. MIT License.
