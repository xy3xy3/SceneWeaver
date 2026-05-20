import json
import os
import socket
import subprocess
from pathlib import Path


def send_command(host="localhost", port=12345, command=None):
    """Send a single command to the Blender socket server"""
    try:
        # Create socket connection
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))

        # Send command
        command_json = json.dumps(command)
        client_socket.send(command_json.encode("utf-8"))

        # Receive response
        response = client_socket.recv(1024)
        response_data = json.loads(response.decode("utf-8"))

        print(f"Sent: {command}")
        print(f"Response: {response_data}")

        return response_data

    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        if "client_socket" in locals():
            client_socket.close()


def update_infinigen(
    action,
    iter,
    json_name,
    ideas=None,
    description=None,
    inplace=False,
    invisible=False,
):
    j = {
        "iter": iter,
        "action": action,
        "json_name": json_name,
        #  "roomsize": roomsize,
        "description": description,
        "inplace": inplace,
        "success": False,
        "ideas": ideas,
    }
    save_dir = os.getenv("save_dir")
    argsfile = f"{save_dir}/args.json"
    with open(argsfile, "w") as f:
        json.dump(j, f, indent=4)
    os.system(
        f"cp {save_dir}/roominfo.json ../run/roominfo.json"
    )

    def get_infinigen_python():
        env_python = os.getenv("INFINIGEN_PYTHON")
        if env_python and Path(env_python).exists():
            return env_python

        roots = []
        conda_exe = os.getenv("CONDA_EXE")
        if conda_exe:
            conda_path = Path(conda_exe).expanduser().resolve()
            roots.extend([conda_path.parent.parent, conda_path.parent])

        for dirname in ("miniforge3", "mambaforge", "miniconda3", "anaconda3"):
            roots.append(Path.home() / dirname)

        seen = set()
        for root in roots:
            root = Path(root)
            if root in seen:
                continue
            seen.add(root)
            candidate = root / "envs/infinigen/bin/python"
            if candidate.exists():
                return str(candidate)

        raise FileNotFoundError(
            "Could not locate infinigen python. Set INFINIGEN_PYTHON explicitly."
        )

    # # if invisible:
    sw_dir = os.getenv("sceneweaver_dir")
    socket = os.getenv("socket")
    if action == "export_supporter" or socket=="False":
        cmd = [
            get_infinigen_python(),
            "-m",
            "infinigen_examples.generate_indoors",
            "--seed",
            "0",
            "--save_dir",
            save_dir,
            "--task",
            "coarse",
            "--output_folder",
            "outputs/indoors/coarse_expand_whole_nobedframe",
            "-g",
            "fast_solve.gin",
            "overhead.gin",
            "studio.gin",
            "-p",
            "compose_indoors.terrain_enabled=False",
            "compose_indoors.invisible_room_ceilings_enabled=True",
        ]
        log_path = Path(sw_dir) / "run.log"
        with open(log_path, "w") as log_file:
            subprocess.run(
                cmd,
                cwd=sw_dir,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                check=True,
            )
        # else:
        #     os.system("bash -i ~/workspace/SceneWeaver/run.sh > run.log 2>&1")
    else:
        command = {
            "action": action,
            "iter": iter,
            "description": description,
            "save_dir": save_dir,
            "json_name": json_name,
            "inplace": inplace,
        }
        # Send command
        response = send_command("localhost", 12345, command)

    with open(argsfile, "r") as f:
        j = json.load(f)

    args_dir = Path(save_dir) / "args"
    args_dir.mkdir(parents=True, exist_ok=True)
    with open(args_dir / f"args_{iter}.json", "w") as f:
        json.dump(j, f, indent=4)

    assert j["success"]
    print("infinigen success")
    return j["success"]
