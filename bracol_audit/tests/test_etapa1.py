import zipfile
import pytest
import pandas as pd
from pathlib import Path
from bracol_audit.audit import BracolAuditEngine
from bracol_audit.loaders.metadata_loader import MetadataLoader
from bracol_audit.loaders.image_loader import ImageLoader


@pytest.fixture
def temp_dataset(tmp_path):
    """Cria uma base válida fictícia em diretório temporário para testes."""
    csv_path = tmp_path / "metadata.csv"
    df = pd.DataFrame({
        "image_id": [101, 102],
        "predominant_stress": [1, 2],
        "miner": [1, 0],
        "rust": [0, 1],
        "phoma": [0, 0],
        "cercospora": [0, 0],
        "severity": [10.5, 20.0]
    })
    df.to_csv(csv_path, index=False)

    img_dir = tmp_path / "images"
    img_dir.mkdir()
    (img_dir / "leaf_01.jpg").write_bytes(b"dummy image 1 content")
    (img_dir / "leaf_02.png").write_bytes(b"dummy image 2 content")

    return csv_path, img_dir


@pytest.fixture
def temp_zip_dataset(tmp_path):
    """Cria uma base válida fictícia em arquivo ZIP para testes."""
    csv_path = tmp_path / "metadata.csv"
    df = pd.DataFrame({
        "predominant_stress": [1],
        "miner": [0],
        "rust": [0],
        "phoma": [0],
        "cercospora": [0],
        "severity": [0.0]
    })
    df.to_csv(csv_path, index=False)

    zip_path = tmp_path / "images.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("img_01.jpeg", b"dummy zip image data")

    return csv_path, zip_path


def test_base_valida_diretorio(temp_dataset):
    csv_path, img_dir = temp_dataset
    engine = BracolAuditEngine()
    df, inventory = engine.run_etapa1(csv_path, img_dir)

    assert df is not None
    assert inventory.metadata_validation.is_valid is True
    assert inventory.metadata_validation.total_rows == 2
    assert inventory.total_images == 2
    filenames = {img.filename for img in inventory.images_found}
    assert "leaf_01.jpg" in filenames
    assert "leaf_02.png" in filenames


def test_base_valida_zip(temp_zip_dataset):
    csv_path, zip_path = temp_zip_dataset
    engine = BracolAuditEngine()
    df, inventory = engine.run_etapa1(csv_path, zip_path)

    assert inventory.metadata_validation.is_valid is True
    assert inventory.total_images == 1
    assert inventory.images_found[0].filename == "img_01.jpeg"


def test_csv_sem_coluna_obrigatoria(tmp_path):
    csv_path = tmp_path / "invalid_metadata.csv"
    df = pd.DataFrame({
        "image_id": [1],
        "predominant_stress": [1]  # Ausentes as demais colunas obrigatórias
    })
    df.to_csv(csv_path, index=False)

    img_dir = tmp_path / "images"
    img_dir.mkdir()

    engine = BracolAuditEngine()
    _, inventory = engine.run_etapa1(csv_path, img_dir)

    assert inventory.metadata_validation.is_valid is False
    assert "miner" in inventory.metadata_validation.missing_mandatory_columns


def test_repeticao_auditoria_determinismo(temp_dataset):
    csv_path, img_dir = temp_dataset
    engine = BracolAuditEngine()

    _, inv1 = engine.run_etapa1(csv_path, img_dir)
    _, inv2 = engine.run_etapa1(csv_path, img_dir)

    assert inv1.total_images == inv2.total_images
    assert inv1.metadata_validation.is_valid == inv2.metadata_validation.is_valid
    assert [x.filename for x in inv1.images_found] == [x.filename for x in inv2.images_found]