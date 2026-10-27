import json
import shutil
import zipfile
from pathlib import Path
from typing import Union, List, Optional
import pandas as pd

from bracol_audit.models import Etapa1Inventory, Etapa2Result, Etapa3Result
from bracol_audit.loaders.metadata_loader import MetadataLoader
from bracol_audit.loaders.image_loader import ImageLoader


class BracolAuditEngine:
    """Núcleo coordenador do processo de auditoria do dataset BRACOL."""

    def __init__(self, mandatory_columns: Optional[List[str]] = None):
        self.metadata_loader = MetadataLoader(mandatory_columns=mandatory_columns)
        self.image_loader = ImageLoader()

    def run_etapa1(self, csv_path: Union[str, Path], images_source_path: Union[str, Path]) -> tuple[Optional[pd.DataFrame], Etapa1Inventory]:
        """Executa a Etapa 1: Leitura e inventário de metadados e ficheiros de imagem."""
        df, meta_result = self.metadata_loader.load_and_validate(csv_path)

        images = []
        if Path(images_source_path).exists():
            images = self.image_loader.inspect_source(images_source_path)

        inventory = Etapa1Inventory(
            metadata_validation=meta_result,
            images_found=images,
            total_images=len(images)
        )

        return df, inventory

    def run_etapa2(
        self,
        csv_path: Union[str, Path],
        images_source_path: Union[str, Path],
        ignore_code: int = 5
    ) -> Etapa2Result:
        """Executa a Etapa 2: Cruzamento ignorando os registos contendo o código 5."""
        df, inventory = self.run_etapa1(csv_path, images_source_path)

        if df is None or not inventory.metadata_validation.is_valid:
            raise ValueError(f"Não foi possível executar a Etapa 2. Erro no CSV: {inventory.metadata_validation.error_message}")

        total_csv_original = len(df)
        code_col = "predominant_stress" if "predominant_stress" in df.columns else None

        if code_col:
            df_filtered = df[df[code_col] != ignore_code].copy()
            ignored_count = len(df) - len(df_filtered)
        else:
            df_filtered = df.copy()
            ignored_count = 0

        id_col = None
        for col in ["image_id", "filename", "image", "id"]:
            if col in df_filtered.columns:
                id_col = col
                break

        if id_col:
            csv_image_ids = set(df_filtered[id_col].astype(str).str.strip().str.lower())
        else:
            csv_image_ids = set(df_filtered.iloc[:, 0].astype(str).str.strip().str.lower())

        physical_images = inventory.images_found
        physical_stems = {Path(img.filename).stem.lower(): img.filename for img in physical_images}
        physical_filenames = {img.filename.lower(): img.filename for img in physical_images}

        matched_csv = set()
        csv_orfaos = []

        for csv_id in csv_image_ids:
            clean_id = Path(csv_id).stem.lower()
            if csv_id in physical_filenames or clean_id in physical_stems:
                matched_csv.add(csv_id)
            else:
                csv_orfaos.append(csv_id)

        imagens_nao_catalogadas = []
        for img in physical_images:
            stem = Path(img.filename).stem.lower()
            fname = img.filename.lower()
            if stem not in physical_stems and fname not in csv_image_ids and stem not in csv_image_ids:
                imagens_nao_catalogadas.append(img.filename)

        return Etapa2Result(
            total_csv_original=total_csv_original,
            total_csv_filtrado=len(df_filtered),
            total_codigo_5_ignorados=ignored_count,
            total_imagens_fisicas=len(physical_images),
            total_correspondencias=len(matched_csv),
            csv_orfaos=csv_orfaos,
            imagens_nao_catalogadas=imagens_nao_catalogadas
        )

    def run_etapa3(
        self,
        csv_path: Union[str, Path],
        images_source_path: Union[str, Path],
        output_dir: Union[str, Path],
        ignore_code: int = 5,
        copy_images: bool = True
    ) -> Etapa3Result:
        """Executa a Etapa 3: Exportação do CSV limpo, relatório JSON e isolamento de imagens."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        images_out_dir = output_path / "images"

        df, inventory = self.run_etapa1(csv_path, images_source_path)
        etapa2_res = self.run_etapa2(csv_path, images_source_path, ignore_code=ignore_code)

        # 1. Filtrar DataFrame mantendo apenas correspondências válidas
        code_col = "predominant_stress" if "predominant_stress" in df.columns else None
        if code_col:
            df_clean = df[df[code_col] != ignore_code].copy()
        else:
            df_clean = df.copy()

        id_col = None
        for col in ["image_id", "filename", "image", "id"]:
            if col in df_clean.columns:
                id_col = col
                break

        physical_stems = {Path(img.filename).stem.lower(): img for img in inventory.images_found}
        physical_filenames = {img.filename.lower(): img for img in inventory.images_found}

        def is_valid_match(row):
            val = str(row[id_col] if id_col else row.iloc[0]).strip().lower()
            clean_val = Path(val).stem.lower()
            return val in physical_filenames or clean_val in physical_stems

        df_final = df_clean[df_clean.apply(is_valid_match, axis=1)].copy()

        # Exportar CSV Limpo
        clean_csv_file = output_path / "dataset_limpo.csv"
        df_final.to_csv(clean_csv_file, index=False)

        # 2. Copiar/Isolar imagens correspondidas
        copied_count = 0
        if copy_images:
            images_out_dir.mkdir(parents=True, exist_ok=True)
            matched_img_objects = set()

            for _, row in df_final.iterrows():
                val = str(row[id_col] if id_col else row.iloc[0]).strip().lower()
                clean_val = Path(val).stem.lower()
                img_obj = physical_filenames.get(val) or physical_stems.get(clean_val)
                if img_obj:
                    matched_img_objects.add(img_obj)

            src_path = Path(images_source_path)
            if src_path.is_dir():
                for img in matched_img_objects:
                    src_file = src_path / img.relative_path
                    dst_file = images_out_dir / img.filename
                    shutil.copy2(src_file, dst_file)
                    copied_count += 1
            elif src_path.is_file() and src_path.suffix.lower() == ".zip":
                with zipfile.ZipFile(src_path, 'r') as zf:
                    for img in matched_img_objects:
                        zf.extract(img.relative_path, images_out_dir)
                        copied_count += 1

        # 3. Exportar Relatório em JSON
        summary_json_file = output_path / "relatorio_auditoria.json"
        summary_data = {
            "total_csv_original": etapa2_res.total_csv_original,
            "total_codigo_5_ignorados": etapa2_res.total_codigo_5_ignorados,
            "total_csv_filtrado": etapa2_res.total_csv_filtrado,
            "total_imagens_fisicas": etapa2_res.total_imagens_fisicas,
            "total_correspondencias_validas": etapa2_res.total_correspondencias,
            "csv_orfaos_count": len(etapa2_res.csv_orfaos),
            "imagens_nao_catalogadas_count": len(etapa2_res.imagens_nao_catalogadas),
            "csv_limpo_gerado": str(clean_csv_file),
            "imagens_isoladas_count": copied_count
        }

        with open(summary_json_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=4, ensure_ascii=False)

        return Etapa3Result(
            etapa2_summary=etapa2_res,
            csv_output_path=str(clean_csv_file),
            summary_output_path=str(summary_json_file),
            copied_images_count=copied_count,
            images_output_dir=str(images_out_dir)
        )