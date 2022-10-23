# pvr_decrypter

Decrypt pvr.ccz to png with content protection key

## Requirements

- [TexturePacker CLI](https://www.codeandweb.com/texturepacker)

## Usage

Run pvr_decrypter with python 3.x or executable in release.
```shell
usage: pvr_decrypter.py [-h] [-k KEY] [-s] input output

Decrypt pvr.ccz to png with content protection key

positional arguments:
  input              path to input .pvr.ccz
  output             path to output .png

optional arguments:
  -h, --help         show this help message and exit
  -k KEY, --key KEY  content protection key
  -s, --suppress     suppress output from TexturePacker
```
For example:
```shell
pvr_decrypter.py input.pvr.ccz output.png -k CONTENT_PROTECTION_KEY
```

## Script
```python
from pvr_decrypter import pvr_to_png
pvr_path = "input.pvr.ccz"
png_path = "output.png"
key = "CONTENT_PROTECTION_KEY"
pvr_to_png(pvr_path, png_path, key)
```

