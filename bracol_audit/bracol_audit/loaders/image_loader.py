import os
import zipfile
from pathlib import Path
from typing import List, Union
from bracol_audit.models import ImageFileInfo

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


class ImageLoader:
    """Classe responsável por inspecionar imagens em pastas locais ou arquivos ZIP."""

    @staticmethod
    def inspect_source(source_path: Union[str, Path]) -> List[ImageFileInfo]:
        path = Path(source_path)

        if not path.exists():
            raise FileNotFoundError(f"Origem de imagens não encontrada: {path}")

        if path.is_file() and path.suffix.lower() == ".zip":
            return ImageLoader._inspect_zip(path)
        elif path.is_dir():
            return ImageLoader._inspect_directory(path)
        else:
            raise ValueError(f"Origem de imagens inválida. Deve ser diretório ou ZIP: {path}")

    @staticmethod
    def _inspect_directory(dir_path: Path) -> List[ImageFileInfo]:
        images = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(dir_path)
                    images.append(
                        ImageFileInfo(
                            filename=file,
                            relative_path=str(rel_path),
                            extension=ext,
                            size_bytes=full_path.stat().st_size
                        )
                    )
        return images

    @staticmethod
    def _inspect_zip(zip_path: Path) -> List[ImageFileInfo]:
        images = []
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                ext = Path(info.filename).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    filename = Path(info.filename).name
                    images.append(
                        ImageFileInfo(
                            filename=filename,
                            relative_path=info.filename,
                            extension=ext,
                            size_bytes=info.file_size
                        )
                    )
        return images