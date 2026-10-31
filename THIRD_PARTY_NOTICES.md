# Third-party notices

This project is licensed under the GNU General Public License v3.0 — see
[LICENSE](LICENSE). Binary builds additionally bundle the components below.

Corresponding source for the GPL-covered work is available at:
<https://github.com/socrabs151/ryzen-temp-limit>

## zenmaster 1.2.1

- Upstream: <https://github.com/HorizonUnix/ZenMaster>
- License: GPL-3.0-only
- Purpose: SMU access and power/thermal management backend.
- The upstream license text is included in builds at
  `_internal/zenmaster-1.2.1.dist-info/licenses/LICENSE`.

## PyInstaller bootloader

- Upstream: <https://pyinstaller.org/>
- License: GPL-2.0-or-later with the special exception that allows distributing
  bundled applications under any license.
- Only the bootloader is bundled; PyInstaller itself is not part of this
  project's source.

## Python 3.12 runtime

- Upstream: <https://www.python.org/>
- License: PSF License Agreement.

## Tcl/Tk 8.6

- Upstream: <https://www.tcl.tk/>
- License: BSD-style.

## OpenSSL 3 (libcrypto, libssl)

- Upstream: <https://www.openssl.org/>
- License: Apache License 2.0.

## libffi

- Upstream: <https://github.com/libffi/libffi>
- License: MIT.

## Expat

- Upstream: <https://github.com/libexpat/libexpat>
- License: MIT.

## zlib

- Upstream: <https://zlib.net/>
- License: zlib License.

## bzip2

- Upstream: <https://sourceware.org/bzip2/>
- License: bzip2 license (BSD-style).

## XZ Utils / liblzma

- Upstream: <https://tukaani.org/xz/>
- License: 0BSD / public domain.

## Pillow

- Upstream: <https://python-pillow.org/>
- Used only at build time to generate the application icon; not bundled.
- License: MIT-CMU.

Full license texts for the Python runtime and its bundled libraries are shipped
with the Python distribution and remain available from the upstream projects
listed above.
