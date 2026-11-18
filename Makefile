# Rebuild, validate and analyse ERGON.  `make all` reproduces every released file.
PY ?= python3
EXT ?= external   # folder with clones of grambank, wals, autotyp-data and atlas-data (optional)

all: cldf validate analysis xlsx

cldf:
	$(PY) scripts/build_cldf.py

validate:
	cldf validate cldf/StructureDataset-metadata.json
	$(PY) scripts/validate.py

xlsx:
	$(PY) scripts/export_xlsx.py

analysis:
	$(PY) scripts/technical_validation.py $(if $(wildcard $(EXT)/grambank),--external $(EXT),)

external:
	mkdir -p external
	# commits used for the figures and tables of the v1.1.0 Data Descriptor (outputs/external_versions.json)
	git clone https://github.com/grambank/grambank external/grambank && git -C external/grambank checkout 37f73da55cf8b426c82383f46a972bc59ce6cf76
	git clone https://github.com/cldf-datasets/wals external/wals && git -C external/wals checkout 81298aa26d01fdc11b769bcc7fa87ad9e43d7ccd
	git clone https://github.com/autotyp/autotyp-data external/autotyp-data && git -C external/autotyp-data checkout a8f294f4810ed882ae6dbffa4e5490e3bafa041e
	git clone https://github.com/davidainman/atlas-data external/atlas-data && git -C external/atlas-data checkout eb038884306061c798c6149b137008fc23c3d403

.PHONY: xlsx all cldf validate analysis external
