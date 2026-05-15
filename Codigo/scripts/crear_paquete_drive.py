# -*- coding: utf-8 -*-
"""Crea un paquete limpio para compartir por Google Drive."""

from pathlib import Path
import shutil

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_MIP = ROOT / "output" / "matrices_insumo_producto"
SHARE_ROOT = ROOT / "output" / "compartir_gmail"
PACKAGE_DIR = SHARE_ROOT / "Paquete_MIP_CEPAL_GoogleDrive"
ZIP_PATH = SHARE_ROOT / "Paquete_MIP_CEPAL_GoogleDrive.zip"


def safe_rmtree(path: Path) -> None:
    resolved = path.resolve()
    allowed = SHARE_ROOT.resolve()
    if allowed not in resolved.parents and resolved != allowed:
        raise RuntimeError(f"Ruta fuera de carpeta compartible: {resolved}")
    if path.exists():
        shutil.rmtree(path)


def copy_code_folder() -> None:
    code_dir = PACKAGE_DIR / "Codigo"
    code_dir.mkdir(parents=True, exist_ok=True)

    files = [
        "main.py",
        "INSTRUCCIONES_DESCARGA.md",
        "FUENTES_EXTERNAS_HISTORICO.md",
    ]
    dirs = ["src", "scripts", "docs"]

    for name in files:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, code_dir / name)

    ignore = shutil.ignore_patterns(
        "__pycache__",
        "*.pyc",
        "generar_ppt_banco.py",
        ".git",
        ".venv",
        "venv",
        "node_modules",
    )
    for name in dirs:
        src = ROOT / name
        dest = code_dir / name
        if src.exists():
            shutil.copytree(src, dest, ignore=ignore)

    readme = [
        "# Codigo del pipeline MIP CEPAL",
        "",
        "Esta carpeta contiene el codigo necesario para regenerar las matrices desde las fuentes locales.",
        "",
        "## Estructura",
        "",
        "- `main.py`: entrada principal del pipeline.",
        "- `src/`: conversion COU a MIP, multiplicadores y parsers por pais.",
        "- `scripts/`: validacion, generacion de Excel y armado de paquetes.",
        "- `docs/`: metodologia del pipeline.",
        "",
        "## Uso basico",
        "",
        "```text",
        "python main.py --pais argentina",
        "python main.py --pais brasil",
        "python main.py --pais mexico",
        "python main.py --pais uruguay",
        "python scripts/validar_mips.py",
        "python scripts/generar_paquete_matrices.py",
        "python scripts/crear_paquete_drive.py",
        "```",
        "",
        "Nota: esta carpeta no incluye `data/raw` ni archivos fuente pesados. Es codigo y documentacion del pipeline.",
    ]
    (code_dir / "README_CODIGO.md").write_text("\n".join(readme), encoding="utf-8")


def copy_mip_files() -> pd.DataFrame:
    rows = []
    mip_dir = PACKAGE_DIR / "MIP"
    mip_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(SOURCE_MIP.glob("*/*.xlsx")):
        if path.name.startswith("~$"):
            continue
        country = path.parent.name
        year = "".join(ch for ch in path.stem if ch.isdigit())[-4:]
        dest_dir = mip_dir / country
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / path.name
        shutil.copy2(path, dest)
        rows.append(
            {
                "pais": country,
                "anio": int(year) if year else None,
                "archivo": str(dest.relative_to(PACKAGE_DIR)),
                "fuente_excel": str(path.relative_to(ROOT)),
            }
        )

    index = pd.DataFrame(rows).sort_values(["pais", "anio", "archivo"])
    index.to_csv(PACKAGE_DIR / "indice_matrices.csv", index=False, encoding="utf-8-sig")
    index.to_excel(PACKAGE_DIR / "indice_matrices.xlsx", index=False)
    return index


def copy_documentation() -> None:
    docs = [
        (ROOT / "docs" / "metodologia_mip.md", PACKAGE_DIR / "METODOLOGIA.md"),
        (ROOT / "presentacion.html", PACKAGE_DIR / "Presentacion_MIP_CEPAL.html"),
        (ROOT / "output" / "tablas" / "validacion_matematica_mip.xlsx", PACKAGE_DIR / "validacion_matematica_mip.xlsx"),
        (ROOT / "output" / "tablas" / "validacion_matematica_mip.md", PACKAGE_DIR / "validacion_matematica_mip.md"),
    ]
    for src, dest in docs:
        if src.exists():
            shutil.copy2(src, dest)


def write_readme(index: pd.DataFrame) -> None:
    countries = index.groupby("pais")["anio"].agg(["count", "min", "max"]).reset_index()
    rows = [
        "# Paquete MIP CEPAL para Google Drive",
        "",
        "Estructura pensada para consulta por un equipo que trabaja con Gmail/Google Drive.",
        "",
        "```text",
        "Paquete_MIP_CEPAL_GoogleDrive/",
        "  MIP/",
        "    Argentina/",
        "    Brasil/",
        "    Mexico/",
        "    Uruguay/",
        "  Codigo/",
        "  Presentacion_MIP_CEPAL.html",
        "  METODOLOGIA.md",
        "  indice_matrices.xlsx",
        "  validacion_matematica_mip.xlsx",
        "```",
        "",
        "## Cobertura",
        "",
    ]
    for row in countries.itertuples(index=False):
        rows.append(f"- {row.pais}: {row.count} matrices ({row.min}-{row.max}).")
    rows += [
        "",
        f"Total de matrices: {len(index)}",
        "",
        "## Nota de uso",
        "",
        "Para navegar en Drive, abrir `MIP/{Pais}/` y seleccionar el Excel del anio requerido.",
        "La carpeta `Codigo/` contiene el pipeline y scripts usados para regenerar la base.",
    ]
    (PACKAGE_DIR / "README.md").write_text("\n".join(rows), encoding="utf-8")


def zip_package() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    shutil.make_archive(str(ZIP_PATH.with_suffix("")), "zip", PACKAGE_DIR)


def main() -> None:
    SHARE_ROOT.mkdir(parents=True, exist_ok=True)
    safe_rmtree(PACKAGE_DIR)
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    index = copy_mip_files()
    copy_code_folder()
    copy_documentation()
    write_readme(index)
    zip_package()

    print(f"[OK] {PACKAGE_DIR}")
    print(f"[OK] {ZIP_PATH}")
    print(f"[OK] matrices copiadas: {len(index)}")


if __name__ == "__main__":
    main()
