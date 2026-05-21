import os
import sys

import bpy

from infinigen_examples.steps import record
from infinigen_examples.steps.tools import render_scene


class DummyStageExecutor:
    def run_stage(self, _name, fn, *args, **kwargs):
        kwargs.pop("use_chance", None)
        kwargs.pop("prereq", None)
        kwargs.pop("default", None)
        kwargs.pop("use_retry", None)
        return fn(*args, **kwargs)


def main():
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1 :]
    else:
        argv = []

    if len(argv) < 2:
        raise SystemExit(
            "Usage: blender --python run/rerender_single_scene.py -- <save_dir> <iter>"
        )

    save_dir = os.path.abspath(os.path.expanduser(argv[0]))
    iter_idx = int(argv[1])

    os.environ["save_dir"] = save_dir
    os.environ.setdefault("JSON_RESULTS", "")
    os.environ["SCENEWEAVER_RENDER_PERSPECTIVE"] = "true"

    state, solver, terrain, house_bbox, solved_bbox, _ = record.load_scene(iter_idx)
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.cycles.preview_samples = 32
    camera_rigs = [bpy.data.objects.get("CameraRigs/0")]
    if camera_rigs[0] is None:
        raise RuntimeError("CameraRigs/0 not found in loaded scene.")

    filename = os.path.join(
        save_dir, "record_scene", f"render_{iter_idx}_recheck.jpg"
    )
    render_scene(
        DummyStageExecutor(),
        solved_bbox,
        camera_rigs,
        state,
        solver,
        filename=filename,
        transparent=False,
    )
    print(f"Rendered {filename}")


if __name__ == "__main__":
    main()
