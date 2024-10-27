import os
import subprocess
from pathlib import Path
from time import strftime

MAX_FILES = int(os.environ.get("PG_BACKUP_MAX_FILES", 10))
path = Path(__file__).resolve().parent


def run_cmd(cmd):
    p = subprocess.Popen(
        ("bash", "-c", cmd),
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    p.wait()
    return p.returncode


def get_time():
    return strftime("%Y%m%d%H")


if __name__ == "__main__":
    print(f"[{get_time()}] Starting backup...")

    with open(path / "servers.conf", "r") as f:
        servers = f.read().splitlines()

    for server in servers:
        if not server or server.startswith("#") or server.isspace():
            continue
        name, host, port, user, password, database = server.split("\t")

        print(f"Current trying {name}...")

        dir = Path(path / "data" / name)
        dir.mkdir(parents=True, exist_ok=True)
        if database == "*":
            file = dir / f"{get_time()}.sql.temp"
            cmd = f"PGPASSWORD={password} pg_dumpall -h {host} -p {port} -U {user} > {file.resolve()}"
        else:
            file = dir / f"{get_time()}.{database}.sql.temp"
            cmd = f"PGPASSWORD={password} pg_dump -h {host} -p {port} -U {user} -f {file.resolve()} {database}"

        if run_cmd(cmd) == 0:
            if database == "*":
                file.rename(dir / f"{get_time()}.sql")
            else:
                file.rename(dir / f"{get_time()}.{database}.sql")
        else:
            file.unlink()
            print(f"{name} backup failed!")

        files = list(dir.glob("*.sql"))
        if len(files) > MAX_FILES:
            name_list = [int(file.stem) for file in files]
            name_list.sort()
            # print(name_list)
            for i in name_list[: len(name_list) - MAX_FILES]:
                print(f"Auto removing {name}/{i}.sql")
                (dir / f"{i}.sql").unlink()

        print(f"{name} done successfully!")

    print(f"[{get_time()}] Backup finished.")
