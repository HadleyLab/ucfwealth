import os
from importlib import resources


def load_sql_migrations():
    migrations = []
    for resource in resources.files(__package__).joinpath("sql").iterdir():
        if not resource.is_file():
            continue
        if not resource.name.endswith(".sql"):
            continue
        with resource.open("r") as f:
            migrations.append(
                {"id": os.path.splitext(resource.name)[0], "sql": f.read()}
            )
    return sorted(migrations, key=lambda m: m["id"])
