import fastapi, os
from render import Text2ImgRender, ScreenshotOptions
from dataclasses import dataclass

app = fastapi.FastAPI()
render = Text2ImgRender()

@dataclass
class Result():
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
    '''
    html: str
    options: ScreenshotOptions
    '''
    
    data = await request.json()
    is_json_return = False
    if "json" in data:
        is_json_return = data["json"]
    if 'tmpl' in data:
        tmpl = data['tmpl']
        data = data['tmpldata']
        html_file_path, abs_path = await render.from_jinja_template(tmpl, data)
    elif 'html' in data:
        html = data["html"]
        html_file_path, abs_path = await render.from_html(html)
    else:
        return Result(code=1, message="html or tmpl not found", data={})
    options = ScreenshotOptions(**data["options"]) if "options" in data else ScreenshotOptions()
    
    pic = await render.html2pic(abs_path, options)

    if is_json_return:
        return Result(code=0, message="success", data={
            "id": pic
        })
    else:
        return fastapi.responses.FileResponse(pic, media_type="image/jpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8999)