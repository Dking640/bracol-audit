import pytest
import pandas as pd
import json
from pathlib import Path
from bracol_audit.audit import BracolAuditEngine


@pytest.fixture
def temp_etapa3_dataset(tmp_path):
    csv_path = tmp_path / "dataset.csv"
    df = pd.DataFrame({
        "image_id": ["101", "102", "103", "104"],
        "predominant_stress": [1, 2, 5, 1],  # 103 tem codigo 5, 104 é orfao
        "miner": [1, 0, 0, 1],
        "rust": [0, 1, 0, 0],
        "phoma": [0, 0, 0, 0],
        "cercospora": [0, 0, 0, 0],
        "severity": [10.0, 15.0, 0.0, 5.0]
    })
    df.to_csv(csv_path, index=False)

    img_dir = tmp_path / "images"
    img_dir.mkdir()
    (img_dir / "101.jpg").write_bytes(b"image 101 content")
    (img_dir / "102.jpg").write_bytes(b"image 102 content")
    (img_dir / "103.jpg").write_bytes(b"image 103 content")

    out_dir = tmp_path / "output"

    return csv_path, img_dir, out_dir


def test_etapa3_pipeline_completo(temp_etapa3_dataset):
    csv_path, img_dir, out_dir = temp_etapa3_dataset
    engine = BracolAuditEngine()

    res = engine.run_etapa3(csv_path, img_dir, out_dir, ignore_code=5, copy_images=True)

    # Verificar criacao dos arquivos
    assert Path(res.csv_output_path).exists()
    assert Path(res.summary_output_path).exists()
    assert Path(res.images_output_dir).exists()

    # Verificar conteudo do CSV Limpo (deve conter apenas 101 e 102 -> 2 linhas)
    df_clean = pd.read_csv(res.csv_output_path)
    assert len(df_clean) == 2
    assert set(df_clean["image_id"].astype(str)) == {"101", "102"}

    # Verificar relatorio JSON
    with open(res.summary_output_path, 'r', encoding='utf-8') as f:
        summary = json.load(f)
    assert summary["total_csv_original"] == 4
    assert summary["total_codigo_5_ignorados"] == 1
    assert summary["total_correspondencias_validas"] == 2

    # Verificar se as 2 imagens foram copiadas
    copied_files = list(Path(res.images_output_dir).glob("*"))
    assert len(copied_files) == 2