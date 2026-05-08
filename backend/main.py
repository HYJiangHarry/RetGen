import os
import random
import math
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PIL import Image, ImageDraw

app = FastAPI(title="Retinal Fundus Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
GENERATED_DIR = os.path.join(STATIC_DIR, "generated")
FRONTEND_DIR = os.path.join(STATIC_DIR, "frontend")
os.makedirs(GENERATED_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

CONDITION_MAP = {
    "Normal fundus": "normal",
    "Diabetic retinopathy": "dr",
    "Age-related macular degeneration": "amd",
    "Glaucoma": "glaucoma",
    "Retinal vein occlusion": "rvo",
    "Pathological myopia": "myopia",
    "Hypertensive retinopathy": "htr",
    "Cataract": "cataract",
    "Optic disc disease": "optic_disc",
    "Macular disease": "macular",
    "Other disease": "other",
}

CONDITION_COLORS = {
    "normal": (200, 80, 50),
    "dr": (220, 50, 50),
    "amd": (180, 120, 40),
    "glaucoma": (100, 180, 60),
    "rvo": (140, 60, 180),
    "myopia": (60, 120, 200),
    "htr": (180, 80, 120),
    "cataract": (200, 160, 80),
    "optic_disc": (80, 160, 160),
    "macular": (160, 100, 160),
    "other": (120, 120, 120),
}


def _generate_placeholder(folder_path: str, filename: str, color: tuple):
    img = Image.new("RGB", (512, 512), (20, 20, 30))
    draw = ImageDraw.Draw(img)
    cx, cy, r = 256, 256, 200
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(40, 30, 20))

    rng = random.Random(filename)
    count = rng.randint(80, 160)
    for _ in range(count):
        a = rng.uniform(0, 360)
        d = rng.uniform(10, 190)
        x = cx + d * math.cos(math.radians(a))
        y = cy + d * math.sin(math.radians(a))
        sz = rng.uniform(1.5, 3.5)
        draw.ellipse([x - sz, y - sz, x + sz, y + sz], fill=color)

    dx = cx + rng.randint(40, 80)
    dy = cy + rng.randint(-50, -10)
    ds = rng.randint(25, 35)
    draw.ellipse([dx - ds, dy - ds, dx + ds, dy + ds], fill=(180, 140, 80))

    img.save(os.path.join(folder_path, filename))


def generate_fundus_image(condition: str) -> str:
    """
    Pick a random fundus image for the given condition from its folder.
    If the folder is empty, auto-generate 5 placeholder images first.
    TODO: Replace with real diffusion model / fundus image generation model.
    """
    folder = CONDITION_MAP.get(condition)
    if folder is None:
        raise ValueError(f"Unknown condition: {condition}")

    folder_path = os.path.join(GENERATED_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)

    images = sorted([
        f for f in os.listdir(folder_path)
        if f.endswith((".png", ".jpg", ".jpeg"))
    ])

    if not images:
        color = CONDITION_COLORS.get(folder, (120, 120, 120))
        for i in range(5):
            _generate_placeholder(folder_path, f"img_{i+1}.png", color)
        images = sorted([
            f for f in os.listdir(folder_path)
            if f.endswith((".png", ".jpg", ".jpeg"))
        ])

    chosen = random.choice(images)
    return f"/static/generated/{folder}/{chosen}"


class GenerateRequest(BaseModel):
    condition: str


class GenerateResponse(BaseModel):
    success: bool
    condition: Optional[str] = None
    image_url: Optional[str] = None
    message: Optional[str] = None


@app.get("/api/status")
def status():
    return {"message": "Retinal Fundus Generator API", "status": "running"}


@app.post("/api/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    condition = req.condition.strip()

    if condition not in CONDITION_MAP:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": f"Unknown condition: '{condition}'. "
                f"Supported: {list(CONDITION_MAP.keys())}",
            },
        )

    try:
        image_url = generate_fundus_image(condition)
        return GenerateResponse(
            success=True,
            condition=condition,
            image_url=image_url,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"Failed to generate image: {str(e)}",
            },
        )


# ---- Frontend SPA serving (production only) ----
FRONTEND_BUILT = os.path.isdir(FRONTEND_DIR)

if FRONTEND_BUILT:
    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/assets/{rest_of_path:path}", include_in_schema=False)
    async def serve_assets(rest_of_path: str):
        file_path = os.path.join(FRONTEND_DIR, "assets", rest_of_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/{rest_of_path:path}", include_in_schema=False)
    async def spa_fallback(rest_of_path: str):
        if rest_of_path.startswith("api/") or rest_of_path.startswith("static/"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"error": "Not found"}, status_code=404)
        file_path = os.path.join(FRONTEND_DIR, rest_of_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
