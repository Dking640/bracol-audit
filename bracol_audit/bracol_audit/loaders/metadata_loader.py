import pandas as pd
from pathlib import Path
from typing import List, Union
from bracol_audit.models import MetadataValidationResult


DEFAULT_MANDATORY_COLUMNS = [
    "predominant_stress",
    "miner",
    "rust",
    "phoma",
    "cercospora",
    "severity",
]


class MetadataLoader:
    """Classe responsável pelo carregamento e validação inicial dos metadados CSV."""

    def __init__(self, mandatory_columns: Union[List[str], None] = None):
        self.mandatory_columns = mandatory_columns or DEFAULT_MANDATORY_COLUMNS

    def load_and_validate(self, csv_path: Union[str, Path]) -> tuple[Union[pd.DataFrame, None], MetadataValidationResult]:
        path = Path(csv_path)

        if not path.exists():
            res = MetadataValidationResult(
                is_valid=False,
                total_rows=0,
                found_columns=[],
                missing_mandatory_columns=self.mandatory_columns,
                error_message=f"Arquivo de metadados não encontrado em: {path}"
            )
            return None, res

        try:
            df = pd.read_csv(path)
        except Exception as e:
            res = MetadataValidationResult(
                is_valid=False,
                total_rows=0,
                found_columns=[],
                missing_mandatory_columns=self.mandatory_columns,
                error_message=f"Erro ao ler o arquivo CSV: {str(e)}"
            )
            return None, res

        found_columns = list(df.columns)
        missing = [col for col in self.mandatory_columns if col not in df.columns]

        is_valid = len(missing) == 0
        error_msg = f"Colunas obrigatórias ausentes: {missing}" if missing else None

        res = MetadataValidationResult(
            is_valid=is_valid,
            total_rows=len(df),
            found_columns=found_columns,
            missing_mandatory_columns=missing,
            error_message=error_msg
        )

        return df, res