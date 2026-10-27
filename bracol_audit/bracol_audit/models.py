from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class ImageFileInfo:
    """Regista as informações físicas de um ficheiro de imagem identificado."""
    filename: str
    relative_path: str
    extension: str
    size_bytes: int


@dataclass
class MetadataValidationResult:
    """Resultado da validação inicial do ficheiro CSV de metadados."""
    is_valid: bool
    total_rows: int
    found_columns: List[str]
    missing_mandatory_columns: List[str]
    error_message: Optional[str] = None


@dataclass
class Etapa1Inventory:
    """Inventário de dados obtido após a execução da Etapa 1."""
    metadata_validation: MetadataValidationResult
    images_found: List[ImageFileInfo] = field(default_factory=list)
    total_images: int = 0


@dataclass
class Etapa2Result:
    """Resultado do cruzamento entre os registos do CSV e as imagens físicas."""
    total_csv_original: int
    total_csv_filtrado: int
    total_codigo_5_ignorados: int
    total_imagens_fisicas: int
    total_correspondencias: int
    csv_orfaos: List[str]
    imagens_nao_catalogadas: List[str]


@dataclass
class Etapa3Result:
    """Resultado do processo de exportação e consolidação da Etapa 3."""
    etapa2_summary: Etapa2Result
    csv_output_path: str
    summary_output_path: str
    copied_images_count: int
    images_output_dir: str