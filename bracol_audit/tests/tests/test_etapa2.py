import pytest
import pandas as pd
from bracol_audit.audit import BracolAuditEngine


@pytest.fixture
def temp_etapa2_dataset(tmp_path):
    """Cria um conjunto fictício contendo registros normais e o código 5."""
    csv_path = tmp_path / "dataset.csv"
    df = pd.DataFrame({
        "image_id": ["101", "102", "103", "104"],
        "predominant_stress": [1, 2, 5, 5],  # 2 registros normais, 2 com código 5
        "miner": [1, 0, 0, 0],
        "rust": [0, 1, 0, 0],
        "phoma": [0, 0, 0, 0],
        "cercospora": [0, 0, 0, 0],
        "severity": [10.0, 15.0, 0.0, 0.0]
    })
    df.to_csv(csv_path, index=False)

    img_dir = tmp_path / "images"
    img_dir.mkdir()
    (img_dir / "101.jpg").write_bytes(b"image 101 content")
    (img_dir / "102.jpg").write_bytes(b"image 102 content")
    (img_dir / "103.jpg").write_bytes(b"image 103 content (codigo 5)")

    return csv_path, img_dir


def test_etapa2_filtragem_codigo_5(temp_etapa2_dataset):
    csv_path, img_dir = temp_etapa2_dataset
    engine = BracolAuditEngine()

    res = engine.run_etapa2(csv_path, img_dir, ignore_code=5)

    assert res.total_csv_original == 4
    assert res.total_codigo_5_ignorados == 2
    assert res.total_csv_filtrado == 2
    assert res.total_correspondencias == 2  # 101 e 102 correspondem


def test_etapa2_registros_orfaos(tmp_path):
    csv_path = tmp_path / "dataset.csv"
    df = pd.DataFrame({
        "image_id": ["201", "202"],
        "predominant_stress": [1, 2],
        "miner": [0, 0],
        "rust": [0, 0],
        "phoma": [0, 0],
        "cercospora": [0, 0],
        "severity": [5.0, 5.0]
    })
    df.to_csv(csv_path, index=False)

    img_dir = tmp_path / "images"
    img_dir.mkdir()
    (img_dir / "201.jpg").write_bytes(b"image 201")  # 202 fica sem imagem física

    engine = BracolAuditEngine()
    res = engine.run_etapa2(csv_path, img_dir, ignore_code=5)

    assert res.total_csv_filtrado == 2
    assert res.total_correspondencias == 1
    assert "202" in res.csv_orfaos