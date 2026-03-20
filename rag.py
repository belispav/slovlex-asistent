# rag.py — alias pre 04_rag.py
# Umožňuje: from rag import ask
# (Python nepodporuje import súborov začínajúcich číslicou priamo)
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

_spec = spec_from_file_location("_rag_impl", Path(__file__).parent / "04_rag.py")
_mod  = module_from_spec(_spec)
_spec.loader.exec_module(_mod)

ask      = _mod.ask
retrieve = _mod.retrieve
generate = _mod.generate
