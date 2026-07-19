import fastapi
import os
import asyncio
from pydantic import BaseModel
from jinja2.exceptions import SecurityError
from fastapi.responses import FileResponse, JSONResponse, Response
from loguru import logger
from .render import Text2ImgRender, ScreenshotOptions
from .storage import create_image_storage
from .util import cleanup_expired_files

app = fastapi.FastAPI()
render = Text2ImgRender()
image_storage = create_image_storage()


class GenerateRequest(BaseModel):
    html: str | None = None
    tmpl: str | None = None
    tmplname: str | None = None
    tmpldata: dict | None = None
    options: ScreenshotOptions | None = None
    json: bool = False


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


@app.get("/text2img/data/{id}")
async def text2img_image(id: str):
    image = await image_storage.get(id)
    if image is None:
        return JSONResponse(
            status_code=404,
            content={"code": 1, "message": "file not found", "data": {}},
        )
    if image.path is not None:
        return FileResponse(image.path, media_type=image.media_type)
    return Response(content=image.content, media_type=image.media_type)


@app.post("/text2img/generate")
async def text2img(request: GenerateRequest):
    """
    html: str
    options: ScreenshotOptions
    """

    is_json_return = request.json or False
    if request.tmpl or request.tmplname:
        if request.tmpl:
            tmpl = request.tmpl
        else:
            tmpl = open(f"tmpl/{request.tmplname}.html", "r", encoding="utf-8").read()
        try:
            _, abs_path = await render.from_jinja_template(tmpl, request.tmpldata or {})
        except SecurityError as e:
            return JSONResponse(
                status_code=400,
                content={"code": 1, "message": f"security error: {str(e)}", "data": {}},
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "code": 1,
                    "message": f"template render error: {str(e)}",
                    "data": {},
                },
            )
    elif request.html:
        html = request.html
        _, abs_path = await render.from_html(html)
    else:
        return JSONResponse(
            status_code=400,
            content={"code": 1, "message": "html or tmpl not found", "data": {}},
        )
    options = (
        request.options
        if request.options
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
        )
    )

    pic = await render.html2pic(abs_path, options)

    if is_json_return:
        try:
            image_id = await image_storage.save(pic)
        except Exception:
            logger.exception("Failed to persist rendered image")
            return JSONResponse(
                status_code=500,
                content={
                    "code": 1,
                    "message": "image storage error",
                    "data": {},
                },
            )
        return JSONResponse(
            content={
                "code": 0,
                "message": "success",
                "data": {"id": image_id},
            },
        )
    else:
        return FileResponse(pic, media_type="image/jpeg")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8999)))
