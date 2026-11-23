"""Build the report DOCX from its editable package or refresh it from Word."""

import argparse
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile


REQUIRED_PARTS = {"[Content_Types].xml", "_rels/.rels", "word/document.xml"}


def build(document: Path, package: Path) -> None:
    files = {
        path.relative_to(package).as_posix(): path
        for path in package.rglob("*")
        if path.is_file() and path.name != ".DS_Store"
    }
    if missing := REQUIRED_PARTS - files.keys():
        raise ValueError(f"Missing document parts: {', '.join(sorted(missing))}")

    with TemporaryDirectory(dir=document.parent) as temporary:
        output = Path(temporary) / document.name
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            for name, path in sorted(files.items()):
                archive.write(path, name)
        output.replace(document)


def extract(document: Path, package: Path) -> None:
    package.parent.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=package.parent) as temporary:
        work = Path(temporary)
        incoming = work / "package"
        backup = work / "previous"
        incoming.mkdir()
        with ZipFile(document) as archive:
            if missing := REQUIRED_PARTS - set(archive.namelist()):
                raise ValueError(f"Missing document parts: {', '.join(sorted(missing))}")
            if any(
                PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
                for name in archive.namelist()
            ):
                raise ValueError("The DOCX contains an invalid part path.")
            archive.extractall(incoming)

        if package.exists():
            package.rename(backup)
        try:
            incoming.rename(package)
        except OSError:
            if backup.exists():
                backup.rename(package)
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "direction",
        choices=("build", "extract"),
        help="Build the DOCX from the source, or replace the source with the current DOCX parts.",
    )
    parser.add_argument("document", type=Path, help="Path to the target DOCX")
    args = parser.parse_args()
    document = args.document.resolve()
    if document.suffix.lower() != ".docx":
        parser.error("The target file must use the .docx extension.")
    package = document.with_suffix(".source") / "package"
    if args.direction == "build":
        build(document, package)
    else:
        extract(document, package)


if __name__ == "__main__":
    main()
