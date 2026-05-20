import json
import os
import socket
import subprocess
import sys
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


def get_blender_binary():
    env_candidates = (
        "SCENEWEAVER_BLENDER",
        "BLENDER_BIN",
        "BLENDER_PATH",
        "INFINIGEN_BLENDER",
    )
    candidates = []
    for env_name in env_candidates:
        env_value = os.getenv(env_name)
        if env_value:
            candidates.append(Path(env_value).expanduser())

    sceneweaver_root = Path(
        os.getenv("sceneweaver_dir", Path(__file__).resolve().parents[3])
    )
    candidates.extend(
        [
            sceneweaver_root / ".local/blender-3.6/blender",
            sceneweaver_root / "blender/blender",
            sceneweaver_root / "Blender.app/Contents/MacOS/Blender",
        ]
    )

    seen = set()
    for candidate in candidates:
        candidate = candidate.expanduser().resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists():
            return str(candidate)

    raise FileNotFoundError(
        "Could not locate blender binary. Set SCENEWEAVER_BLENDER, BLENDER_BIN, or BLENDER_PATH explicitly."
    )


def get_blender_python(blender_binary: str) -> str:
    blender_path = Path(blender_binary).resolve()
    blender_root = blender_path.parent
    candidates = [
        blender_root / "3.6/python/bin/python3.10",
        blender_root / "python/bin/python3.10",
        blender_root / "python/bin/python3",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError(
        f"Could not locate Blender python interpreter near {blender_binary}."
    )


def ensure_blender_package(blender_python: str, package_name: str) -> None:
    probe = subprocess.run(
        [blender_python, "-c", f"import {package_name}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if probe.returncode == 0:
        return

    subprocess.run(
        [
            blender_python,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            package_name,
        ],
        check=True,
    )


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

    # # if invisible:
    sw_dir = os.getenv("sceneweaver_dir")
    socket = os.getenv("socket")
    if action == "export_supporter" or socket=="False":
        sceneweaver_root = Path(
            os.getenv("sceneweaver_dir", Path(__file__).resolve().parents[3])
        ).resolve()
        blender_binary = get_blender_binary()
        blender_python = get_blender_python(blender_binary)
        ensure_blender_package(blender_python, "dill")
        blendscript_path_append = sceneweaver_root / "infinigen/tools/blendscript_path_append.py"
        generate_indoors_script = sceneweaver_root / "infinigen_examples/generate_indoors.py"
        cmd = [
            blender_binary,
            "--background",
            "-noaudio",
            "--python",
            str(blendscript_path_append),
            "--python",
            str(generate_indoors_script),
            "--",
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
        env = os.environ.copy()
        pythonpath_parts = [str(sceneweaver_root)]
        if env.get("PYTHONPATH"):
            pythonpath_parts.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
        with open(log_path, "w") as log_file:
            subprocess.run(
                cmd,
                cwd=str(sceneweaver_root),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
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
