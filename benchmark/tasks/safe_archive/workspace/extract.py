import zipfile


def extract_zip(zip_path, destination):
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(destination)
        return sorted(archive.namelist())
