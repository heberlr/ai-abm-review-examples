#!/usr/bin/env python3
"""
visualize_vtp.py

Simple script to visualize a sequence of VTK PolyData `.vtp` frames and
produce an animated GIF or a sequence of PNGs.

Features:
  - Auto-detects scalar data (cell or point data) for coloring
  - Generates animated GIFs with colorbars
  - Exports frame sequences as PNG files

Dependencies:
  pip install pyvista imageio natsort

Examples:
  python visualize_vtp.py --input "frame*.vtp" --output anim.gif --fps 15
  python visualize_vtp.py --input "frame*.vtp" --scalars neighbors --cmap plasma --output colored.gif
  python visualize_vtp.py --input "frame*.vtp" --png --out-dir frames_png --width 1024 --height 1024

"""
import argparse
import glob
import os
import re
import tempfile
import shutil

import imageio.v2 as imageio
import pyvista as pv

# Simple natural sort by trailing number if filenames use frameNNN.vtp
def _frame_key(path):
    m = re.search(r"(\d+)(?=\.[^.]+$)", os.path.basename(path))
    if m:
        return int(m.group(1))
    return path


def sorted_files(pattern):
    files = glob.glob(pattern)
    return sorted(files, key=_frame_key)


def main():
    p = argparse.ArgumentParser(description="Visualize a sequence of .vtp frames")
    p.add_argument("--input", required=True, help='glob pattern or single file (e.g. "frame*.vtp")')
    p.add_argument("--output", default="animation.gif", help="output GIF filename")
    p.add_argument("--fps", type=float, default=20.0, help="frames per second for GIF")
    p.add_argument("--png", action="store_true", help="emit PNG frames into --out-dir instead of GIF")
    p.add_argument("--out-dir", default="frames_out", help="directory to save PNG frames")
    p.add_argument("--width", type=int, default=800, help="render width")
    p.add_argument("--height", type=int, default=800, help="render height")
    p.add_argument("--show-edges", action="store_true", help="render mesh edges")
    p.add_argument("--scalars", default=None, help="name of array to color by (auto-detected if not set)")
    p.add_argument("--cmap", default="viridis", help="colormap name (default: viridis)")
    args = p.parse_args()

    files = sorted_files(args.input)
    if not files:
        print("No files matched pattern:", args.input)
        return

    # Create output directory or temporary dir
    if args.png:
        os.makedirs(args.out_dir, exist_ok=True)
        writer = None
    else:
        tmpdir = tempfile.mkdtemp(prefix="vtp_frames_")
        writer = imageio.get_writer(args.output, mode='I', duration=1.0 / max(0.1, args.fps))

    try:
        for i, fp in enumerate(files):
            mesh = pv.read(fp)

            # Auto-detect scalars to color by (cell data first, then point data)
            scalars_to_use = None
            scalars_name = None
            
            if args.scalars and args.scalars in mesh.array_names:
                # User-specified array
                scalars_to_use = mesh[args.scalars]
                scalars_name = args.scalars
            else:
                # Auto-detect: prefer cell data, then point data
                available_arrays = [name for name in mesh.array_names]
                
                if available_arrays:
                    # Prefer 'neighbors', then 'area', then first available
                    if 'neighbors' in available_arrays:
                        scalars_name = 'neighbors'
                        scalars_to_use = mesh['neighbors']
                    elif 'area' in available_arrays:
                        scalars_name = 'area'
                        scalars_to_use = mesh['area']
                    else:
                        scalars_name = available_arrays[0]
                        scalars_to_use = mesh[scalars_name]

            plotter = pv.Plotter(off_screen=True, window_size=(args.width, args.height))

            if scalars_to_use is not None:
                plotter.add_mesh(
                    mesh,
                    scalars=scalars_to_use,
                    cmap=args.cmap,
                    show_edges=args.show_edges,
                    scalar_bar_args={'title': scalars_name}
                )
            else:
                plotter.add_mesh(mesh, color='lightgrey', show_edges=args.show_edges)

            # Let PyVista choose a good camera, or you can set plotter.camera_position
            img_path = os.path.join(args.out_dir, f"frame_{i:04d}.png") if args.png else os.path.join(tmpdir, f"frame_{i:04d}.png")
            plotter.show(screenshot=img_path, auto_close=True)
            plotter.close()

            if writer is not None:
                img = imageio.imread(img_path)
                writer.append_data(img)

            print(f"Rendered {i+1}/{len(files)}: {os.path.basename(fp)} (colored by '{scalars_name}')")

    finally:
        if writer is not None:
            writer.close()
            shutil.rmtree(tmpdir, ignore_errors=True)

    if args.png:
        print("Wrote PNG frames to:", os.path.abspath(args.out_dir))
    else:
        print("Wrote GIF:", os.path.abspath(args.output))


if __name__ == '__main__':
    main()
