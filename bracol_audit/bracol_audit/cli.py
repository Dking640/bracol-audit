import argparse
import sys
from bracol_audit.audit import BracolAuditEngine


def main():
    parser = argparse.ArgumentParser(description="BRACOL Audit — Pipeline Completo (Etapas 1, 2 e 3)")
    parser.add_argument("--csv", required=True, help="Caminho para o ficheiro CSV de metadados")
    parser.add_argument("--images", required=True, help="Caminho para a pasta ou ficheiro ZIP de imagens")
    parser.add_argument("--ignore-code", type=int, default=5, help="Código a ser ignorado (Padrão: 5)")
    parser.add_argument("--output-dir", default="./output_bracol", help="Diretório de saída para salvar o dataset limpo e relatórios")
    parser.add_argument("--no-copy-images", action="store_true", help="Desativa a cópia física das imagens para a pasta de saída")

    args = parser.parse_args()

    engine = BracolAuditEngine()

    try:
        resultado = engine.run_etapa3(
            csv_path=args.csv,
            images_source_path=args.images,
            output_dir=args.output_dir,
            ignore_code=args.ignore_code,
            copy_images=not args.no_copy_images
        )

        res2 = resultado.etapa2_summary

        print("\n" + "=" * 60)
        print("          BRACOL AUDIT — RELATÓRIO FINAL CONSOLIDADO")
        print("=" * 60)
        print(f"Total de registos no CSV original:        {res2.total_csv_original}")
        print(f"Registos com código {args.ignore_code} ignorados:         {res2.total_codigo_5_ignorados}")
        print(f"Total de registos no CSV considerados:     {res2.total_csv_filtrado}")
        print(f"Total de imagens físicas encontradas:      {res2.total_imagens_fisicas}")
        print(f"Correspondências válidas encontradas:      {res2.total_correspondencias}")
        print("-" * 60)
        print(f"Registos CSV órfãos (sem imagem):         {len(res2.csv_orfaos)}")
        print(f"Imagens físicas não catalogadas:          {len(res2.imagens_nao_catalogadas)}")
        print("=" * 60)
        print("          ARQUIVOS EXPORTADOS (ETAPA 3)")
        print("=" * 60)
        print(f"-> CSV Limpo:         {resultado.csv_output_path}")
        print(f"-> Relatório JSON:    {resultado.summary_output_path}")
        print(f"-> Imagens Copiadas:  {resultado.copied_images_count} ficheiros em '{resultado.images_output_dir}'")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n[ERRO] Falha ao executar a auditoria: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())