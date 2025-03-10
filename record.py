import asyncio
import argparse
from pathlib import Path
import shutil

import ffmpeg
from playwright.async_api import async_playwright

async def capture_frames(url, width, height, duration, framerate, frames_dir):
    async with async_playwright() as p:
        # go to webpage
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": width, "height": height})
        page = await context.new_page()

        await page.goto(url)
        await page.wait_for_timeout(2000)

        # create frames directory
        frames_dir = Path(frames_dir)
        frames_dir.mkdir(parents=True, exist_ok=True)

        # capture frames
        total_frames = int((duration / 1000) * framerate)
        print(f"Capturing {total_frames} frames...")
        for i in range(total_frames):
            filename = frames_dir / f"frame-{i:04d}.png"
            await page.screenshot(path=str(filename))
            await page.wait_for_timeout(1000 / framerate)

        await browser.close()

def convert_frames_to_video(framerate, output, frames_dir):
    frames_dir = Path(frames_dir)
    print("Converting frames to video using ffmpeg-python...")
    (
        ffmpeg
        .input(frames_dir / "frame-%04d.png", framerate=framerate)
        .output(output, vcodec="rawvideo", pix_fmt="bgr24")
        .overwrite_output()
        .run()
    )
    print(f"Video saved as {output}")

def main():
    parser = argparse.ArgumentParser(
        description="Capture frames from a webpage and convert them to an MP4 video."
    )
    parser.add_argument("--url", type=str, default="http://localhost:3000", help="URL to capture")
    parser.add_argument("--width", type=int, default=1280, help="Viewport width")
    parser.add_argument("--height", type=int, default=720, help="Viewport height")
    parser.add_argument("--duration", type=int, default=5000, help="Capture duration in milliseconds")
    parser.add_argument("--framerate", type=int, default=30, help="Frames per second")
    parser.add_argument("--output", type=str, default="output.mp4", help="Output video filename")
    parser.add_argument("--frames_dir", type=str, default="frames", help="Frames output directory")
    parser.add_argument("--keep_frames", action="store_true", help="Keep frame images")

    args = parser.parse_args()

    asyncio.run(
        capture_frames(
            args.url,
            args.width,
            args.height,
            args.duration,
            args.framerate,
            args.frames_dir,
        )
    )

    convert_frames_to_video(args.framerate, args.output, args.frames_dir)

    if not args.keep_frames:
        frames_dir = Path(args.frames_dir)
        shutil.rmtree(frames_dir)


if __name__ == "__main__":
    main()
