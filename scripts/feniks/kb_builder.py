import json
from pathlib import Path
from typing import List, Dict, Any

from feniks.logger import log
from feniks.types import Chunk
from feniks.utils import ensure_dir


def build_module_cards_from_chunks(chunks: List[Chunk]) -> Dict[str, Any]:
    """Builds module summary cards from the list of chunks."""
    reg: Dict[str, Dict[str, set]] = {}
    for chunk in chunks:
        mkey = chunk.module or "unknown_module"
        reg.setdefault(mkey, {
            "services": set(), "controllers": set(), "factories": set(),
            "directives": set(), "routes": set(), "templates": set(), "files": set()
        })
        reg[mkey]["files"].add(chunk.file_path)

        # Simple classification based on chunk name/type
        if chunk.ast_node_type == "CallExpression":
            name = chunk.chunk_name.lower()
            if name.endswith("service"): 
                reg[mkey]["services"].add(chunk.chunk_name)
            elif name.endswith("ctrl") or name.endswith("controller"): 
                reg[mkey]["controllers"].add(chunk.chunk_name)
            elif name.endswith("factory"): 
                reg[mkey]["factories"].add(chunk.chunk_name)
            elif name.endswith("directive"): 
                reg[mkey]["directives"].add(chunk.chunk_name)
        elif chunk.ast_node_type == "NgTemplate":
            reg[mkey]["templates"].add(Path(chunk.file_path).name)

    # Convert sets to sorted lists for stable JSON output
    cards = {}
    for mkey, data in reg.items():
        cards[mkey] = {k: sorted(list(v)) for k, v in data.items()}
        cards[mkey]["module"] = mkey
    return cards


def write_module_cards(out_dir: Path, modules_card: Dict[str, Any]) -> None:
    """Writes module cards and a manifest file to the output directory."""
    base = out_dir / "kb" / "modules"
    ensure_dir(base)
    for mod, data in modules_card.items():
        (base / f"{mod}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest_path = out_dir / "kb" / "modules_manifest.json"
    manifest = {"modules": sorted(list(modules_card.keys()))}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"Wrote {len(modules_card)} module cards to {base}")
