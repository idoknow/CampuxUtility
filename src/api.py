import fastapi
import os
import asyncio
from loguru import logger
from .render import Text2ImgRender, ScreenshotOptions
from .util import cleanup_expired_files
from dataclasses import dataclass

app = fastapi.FastAPI()
render = Text2ImgRender()


# 启动时创建清理任务
@app.on_event("startup")
async def startup_event():
    """应用启动时的事件处理"""
    # 启动定期清理任务
    asyncio.create_task(periodic_cleanup())
    logger.info("Started periodic cleanup task")


async def periodic_cleanup():
    """定期清理过期文件的后台任务"""
    while True:
        try:
            cleanup_expired_files()
        except Exception as e:
            logger.error(f"Error during periodic cleanup: {e}")
        # 每小时执行一次清理
        await asyncio.sleep(3600)


@dataclass
class Result:
    code: int
    message: str
    data: dict


@app.get("/text2img/data/{id}")
async def text2img_image(id: str):
    pic = f"data/{id}"
    if os.path.exists(pic):
        return fastapi.responses.FileResponse(pic, media_type="image/jpeg")
    else:
        return Result(code=1, message="file not found", data={})


@app.post("/text2img/generate")
async def text2img(request: fastapi.Request):
    """
    html: str
    options: ScreenshotOptions
    """

    data = await request.json()
    is_json_return = False
    if "json" in data:
        is_json_return = data["json"]
    if "tmpl" in data or "tmplname" in data:
        if "tmpl" in data:
            tmpl = data["tmpl"]
        else:
            tmpl = open(f"tmpl/{data['tmplname']}.html", "r", encoding="utf-8").read()
        html_file_path, abs_path = await render.from_jinja_template(
            tmpl, data["tmpldata"]
        )
    elif "html" in data:
        html = data["html"]
        html_file_path, abs_path = await render.from_html(html)
    else:
        return Result(code=1, message="html or tmpl not found", data={})
    options = (
        ScreenshotOptions(**data["options"])
        if "options" in data
        else ScreenshotOptions(
            timeout=None,
            type=None,
            quality=None,
            omit_background=None,
            full_page=True,
            clip=None,
            animations=None,
            caret=None,
            scale=None,
            mask=None,
        )
    )

    pic = await render.html2pic(abs_path, options)

    if is_json_return:
        return Result(code=0, message="success", data={"id": pic.replace("\\", "/")})
    else:
        return fastapi.responses.FileResponse(pic, media_type="image/jpeg")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8999)))
