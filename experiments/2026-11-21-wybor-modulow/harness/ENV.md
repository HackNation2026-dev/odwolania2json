# Środowisko `.venv-exp` (wynik pomiaru, 2026-11-22)

Środowisko eksperymentów leży w `/.venv-exp/` w korzeniu repozytorium (poza Git, wpis w `.gitignore`).
Nie zmienia `requirements*.txt` ani `.venv`; to osobne środowisko do pomiarów.

## Co i jak zainstalowano

- Python **3.13.18** (`uv venv --python 3.13 .venv-exp`; systemowy `python3` to 3.15.2, więc 3.13 pobrał `uv`).
- `uv pip install -r apps/backend/requirements.txt` (zależności projektu, bez zmian wersji).
- OCR CPU: `rapidocr==3.10.0 onnxruntime==1.32.0` (te same wersje, które przypina `apps/backend/requirements-ocr.txt`),
  `pillow numpy opencv-python-headless pytest-cov`, oraz `pypdf` (tylko dlatego, że `syntetyczne.py` z eksperymentu
  przypadków brzegowych go importuje).
- Zmierzony rozmiar: **491 MB** całe środowisko (`du -sm .venv-exp`; największe: opencv headless 81 MB + 93 MB bibliotek,
  onnxruntime 73 MB, numpy 55 MB z bibliotekami, rapidocr 32 MB, pillow 22 MB). Czas instalacji OCR: ok. 55 s (sieć dostępna).

## Wyniki dla decyzji (co działa, co nie)

| Pytanie | Wynik |
|---|---|
| Czy rapidocr i onnxruntime instalują się na Pythonie 3.13? | Tak: gotowe koła `cp313` (onnxruntime-1.32.0-cp313-manylinux_2_28_x86_64), bez kompilacji. |
| GPU lub binarki systemowe? | Nie. Tylko CPU (`onnxruntime`, nie `onnxruntime-gpu`), bez bibliotek systemowych poza glibc/manylinux. |
| Wagi OCR przez pip? | Tak: koło `rapidocr` zawiera trzy pliki ONNX (`PP-OCRv6_det_small` 9,9 MB, `PP-OCRv6_rec_small` 21,2 MB, `ch_ppocr_mobile_v2.0_cls_mobile` 0,6 MB). Pierwsze uruchomienie nie pobiera niczego (sprawdzone: log „File exists and is valid”). Konfiguracja domyślna zawiera jednak adresy `modelscope.cn` jako zapasowe; nie są używane, gdy pliki są w kole. |
| Licencje | `rapidocr` Apache-2.0, `onnxruntime` MIT (metadane pakietów). Licencja i lokalizacja samych wag nie jest potwierdzona w metadanych: do rozstrzygnięcia w ADR-002 (`/system` zwraca `models[].license` z adnotacją „do potwierdzenia”). |
| Zależności przechodnie OCR | `opencv-python-headless` 5.1.0.95 (wciągany przez rapidocr; ok. 170 MB z bibliotekami), `shapely`, `pyclipper`, `omegaconf`, `requests`, `tqdm`, `protobuf`. To głównie wpływa na rozmiar paczki dostarczanej przez pip. |
| Sieć przy instalacji | `uv` domyślnie przekraczał limit czasu na dużych kołach (`files.pythonhosted.org`, „operation timed out”, 4 próby); działa z `UV_CONCURRENT_DOWNLOADS=1 UV_HTTP_TIMEOUT=180`. `curl` do tego samego adresu działał, więc to zachowanie klienta w tej sieci, nie brak dostępu. Dla jury: instalacja wymaga ok. 100 MB pobrań. |
| Szybkość i pamięć OCR (pomiar poglądowy, nie E02) | Skan z szablonu organizatora, 7 stron 1240×1754 pt, render 150 dpi, domyślna konfiguracja onnxruntime: **ok. 24 s łącznie (ok. 3,4 s/stronę)**, szczytowy RSS serwera **ok. 870 MB**. Pojedyncza strona 200 dpi (3446×4873 px): 3,5 s. |
| Polskie znaki | W jednej próbie rozpoznano „ograniczona” zamiast „ograniczoną” (utrata ogonka); w innym miejscu ta sama fraza była poprawna. Skala błędu to zadanie E02 (CER/WER), nie ten pomiar. |

## Limit pamięci procesu serwera

Wykryto w praktyce, że `systemd-run --user --scope -p MemoryMax=14G` działa na tej maszynie (systemd 262): `memory.max` w
cgroup procesu wynosi 15032385536 B (14 GiB). `client.ManagedServer` wybiera metodę automatycznie w kolejności:
`systemd-run` → `prlimit --as=14GiB` → brak limitu (`limit_method: "none"`). Wybrana metoda trafia do każdego pliku
wyniku (`limit_method`). Uwaga: `prlimit --as` limituje przestrzeń adresową, a nie RSS, i bywa ostrzejszy (onnxruntime
rezerwuje dużo pamięci wirtualnej), więc jest tylko zapasową drogą. Szczytowy RSS to `VmHWM` procesu serwera z `/proc`.

Maszyna pomiarowa: 8 rdzeni logicznych, 30 GB RAM (docelowo laptop i7/16 GB bez GPU; czasy nie są przenoszalne 1:1).

## Przypięte wersje (`uv pip freeze`)

```
annotated-doc==0.0.7
annotated-types==0.8.0
anyio==4.16.0
argcomplete==3.7.2
attrs==26.1.0
black==26.10.1
certifi==2026.11.20
charset-normalizer==3.5.2
click==8.5.1
colorlog==6.12.0
coverage==7.17.4
datamodel-code-generator==0.99.0
fastapi==0.165.0
flatbuffers==25.12.19
genson==1.4.0
h11==0.16.0
httpcore==1.0.9
httptools==0.9.0
httpx==0.28.1
idna==3.20
inflect==7.6.0
iniconfig==2.3.1
isort==8.0.1
jaraco-functools==4.6.0
jinja2==3.1.6
jsonschema==4.26.0
jsonschema-path==0.5.0
jsonschema-specifications==2025.9.1
lazy-object-proxy==1.13.0
markupsafe==3.0.4
more-itertools==11.2.1
mypy-extensions==1.2.0
numpy==2.5.5
omegaconf==2.4.0
onnxruntime==1.32.0
openapi-schema-validator==0.9.0
openapi-spec-validator==0.9.0
opencv-python-headless==5.1.0.95
opentelemetry-api==1.45.2
packaging==26.3
pathable==0.6.0
pathspec==1.1.1
pillow==13.0.0
platformdirs==4.14.8
pluggy==1.7.0
protobuf==7.36.2
pyclipper==1.4.0
pydantic==2.14.4
pydantic-core==2.50.5
pydantic-settings==2.16.3
pygments==2.21.0
pypdf==7.1.1
pypdfium2==5.15.2
pytest==9.2.0
pytest-cov==7.1.0
python-dotenv==1.2.4
python-multipart==0.0.34
pytokens==0.4.1
pyyaml==6.0.4
rapidfuzz==3.14.6
rapidocr==3.10.0
referencing==0.37.0
requests==2.34.2
rfc3339-validator==0.1.4
rpds-py==2026.9.1
shapely==2.2.0
six==1.17.0
sqlalchemy==2.1.9
starlette==1.10.0
tqdm==4.70.1
typeguard==4.6.1
typing-extensions==4.16.0
typing-inspection==0.4.5
urllib3==2.8.0
uvicorn==0.54.0
uvloop==0.23.0
watchfiles==1.3.0
websockets==17.4
```
