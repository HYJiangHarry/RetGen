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
    "Normal fundus": ("normal.png", (200, 80, 50)),
    "Diabetic retinopathy": ("dr.png", (220, 50, 50)),
    "Age-related macular degeneration": ("amd.png", (180, 120, 40)),
    "Glaucoma": ("glaucoma.png", (100, 180, 60)),
    "Retinal vein occlusion": ("rvo.png", (140, 60, 180)),
    "Pathological myopia": ("myopia.png", (60, 120, 200)),
    "Hypertensive retinopathy": ("htr.png", (180, 80, 120)),
}


def generate_fundus_image(condition: str) -> str:
    """
    Generate a retinal fundus image for the given condition.

    Currently returns a preset example image.
    TODO: Replace with real diffusion model / fundus image generation model.
    """
    entry = CONDITION_MAP.get(condition)
    if entry is None:
        raise ValueError(f"Unknown condition: {condition}")

    filename, color = entry
    filepath = os.path.join(GENERATED_DIR, filename)

    if not os.path.exists(filepath):
        img = Image.new("RGB", (512, 512), (20, 20, 30))
        draw = ImageDraw.Draw(img)

        cx, cy, r = 256, 256, 200
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(40, 30, 20))

        for _ in range(120):
            angle = random.uniform(0, 360)
            dist = random.uniform(10, 190)
            x = cx + dist * math.cos(math.radians(angle))
            y = cy + dist * math.sin(math.radians(angle))
            draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=color)

        disc_x, disc_y = cx + 60, cy - 30
        draw.ellipse(
            [disc_x - 30, disc_y - 30, disc_x + 30, disc_y + 30],
            fill=(180, 140, 80),
        )

        img.save(filepath)

    return f"/static/generated/{filename}"


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


@app.on_event("startup")
def pregenerate_images():
    for condition in CONDITION_MAP:
        try:
            generate_fundus_image(condition)
        except Exception as e:
            print(f"Warning: failed to pre-generate {condition}: {e}")


# ---- Frontend SPA serving (production only) ----
# Dockerfile puts built frontend at backend/static/frontend/
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

    # SPA fallback for any other unmatched route
    @app.get("/{rest_of_path:path}", include_in_schema=False)
    async def spa_fallback(rest_of_path: str):
        if rest_of_path.startswith("api/") or rest_of_path.startswith("static/"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"error": "Not found"}, status_code=404)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
