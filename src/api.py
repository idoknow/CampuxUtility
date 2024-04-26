import fastapi, os
from render import Text2ImgRender, ScreenshotOptions

app = fastapi.FastAPI()
render = Text2ImgRender()

class Result():
    code: int
    message: str
    data: dict

@app.get("/text2img/image")
async def text2img_image(request: fastapi.Request):
    data = request.query_params
    id = data["id"]
    # 去 data 目录下找到对应的文件
    pic = f"data/{id}"
    if os.path.exists(pic):
        return fastapi.responses.FileResponse(pic, media_type="image/jpeg")
    else:
        return Result(code=1, message="file not found", data={})

@app.post("/text2img/generate")
async def text2img(request: fastapi.Request):
    '''
    html: str
    options: ScreenshotOptions
    '''
    
    data = await request.json()
    is_json_return = False
    if "html" not in data:
        return {"error": "html is required"}
    if "json" in data:
        is_json_return = data["json"]
    html = data["html"]
    options = ScreenshotOptions(**data["options"]) if "options" in data else ScreenshotOptions()
    html_file_path = await render.from_html(html)
    pic = await render.html2pic(html_file_path, options)

    if is_json_return:
        return Result(code=0, message="success", data={
            "id": pic
        })
    else:
        return fastapi.responses.FileResponse(pic, media_type="image/jpeg")