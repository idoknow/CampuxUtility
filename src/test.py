from render import Text2ImgRender, ScreenshotOptions
import requests

def main():
    render = Text2ImgRender()
    template = """<html><head><meta name="viewport" content="width=device-width,initial-scale=1.0"></head><body><h1>{{ title }}😤</h1><p>{{ content }}</p></body></html>"""
    data = {"title": "Hello, World!", "content": "This is a test."}
    html = render.from_jinja_template(template, data)
    pic = render.html2pic(html, ScreenshotOptions(type="jpeg", full_page=True))

    print(f"Rendered HTML to {pic}")


def test_api():
    url = "http://localhost:8000/text2img/generate"
    data = {
        "html": "<html><head><meta name=\"viewport\" content=\"width=device-width,initial-scale=1.0\"></head><body><h1>Hello, World!😤</h1><p>This is a test.</p></body></html>",
        "options": {
            "type": "jpeg",
            "full_page": True
        },
        "json": False
    }
    response = requests.post(url, json=data)
    print(response.json())


if __name__ == "__main__":
    # main()
    test_api()