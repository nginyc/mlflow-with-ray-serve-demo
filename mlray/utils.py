
def validate_python_major_version(version: str):
    parts = version.split(".")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        raise ValueError(f"{version} must be in format 'major.minor', e.g. '3.9'")
    return version

def get_python_major_version(version: str) -> str:
    return '.'.join(version.split('.')[0:2])
    