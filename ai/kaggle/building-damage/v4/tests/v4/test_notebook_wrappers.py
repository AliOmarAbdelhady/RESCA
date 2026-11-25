from __future__ import annotations

import json
from pathlib import Path


def test_v4_kaggle_notebooks_are_thin_deterministic_wrappers() -> None:
    root = Path(__file__).parents[2]
    notebooks = sorted(root.glob("*.ipynb"))

    assert {path.name for path in notebooks} == {
        "00_data_and_split_audit.ipynb",
        "00_gpu_smoke.ipynb",
        "01_dinov3_teacher_profile.ipynb",
        "01_dinov3_vitl_profile.ipynb",
        "02_specialist_manifest_audit.ipynb",
        "03_final_bundle_verify.ipynb",
    }
    for path in notebooks:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["nbformat"] == 4
        source = "\n".join(
            line
            for cell in payload["cells"]
            if cell["cell_type"] == "code"
            for line in cell["source"]
        )
        if path.name == "00_data_and_split_audit.ipynb":
            assert "INPUT_ROOT" in source
            assert "label_schema_ok" in source
        elif path.name == "00_gpu_smoke.ipynb":
            assert "torch.cuda.is_available" in source
            assert "refusing a CPU fallback" in source
        else:
            assert "subprocess.run" in source or "load_" in source
        assert "kaggle_key" not in source.lower()
        assert "hf_token" not in source.lower()
