import logging, os, time

from util import generate_data_path
from pathlib import Path
from playwright.async_api import async_playwright
from jinja2 import Template
from typing_extensions import TypedDict
from playwright.async_api._generated import Locator
from playwright._impl._api_structures import FloatRect
from typing import Literal

class ScreenshotOptions(TypedDict):
    """Playwright 截图参数

    详见：https://playwright.dev/python/docs/api/class-page#page-screenshot

    Args:
        timeout (float, optional): 截图超时时间.
        type (Literal["jpeg", "png"], optional): 截图图片类型.
        path (Union[str, Path]], optional): 截图保存路径，如不需要则留空.
        quality (int, optional): 截图质量，仅适用于 JPEG 格式图片.
        omit_background (bool, optional): 是否允许隐藏默认的白色背景，这样就可以截透明图了，仅适用于 PNG 格式.
        full_page (bool, optional): 是否截整个页面而不是仅设置的视口大小，默认为 True.
        clip (FloatRect, optional): 截图后裁切的区域，xy为起点.
        animations: (Literal["allow", "disabled"], optional): 是否允许播放 CSS 动画.
        caret: (Literal["hide", "initial"], optional): 当设置为 `hide` 时，截图时将隐藏文本插入符号，默认为 `hide`.
        scale: (Literal["css", "device"], optional): 页面缩放设置.
            当设置为 `css` 时，则将设备分辨率与 CSS 中的像素一一对应，在高分屏上会使得截图变小.
            当设置为 `device` 时，则根据设备的屏幕缩放设置或当前 Playwright 的 Page/Context 中的
            device_scale_factor 参数来缩放.
        mask (List["Locator"]], optional): 指定截图时的遮罩的 Locator。元素将被一颜色为 #FF00FF 的框覆盖.

    @author: Redlnn(https://github.com/GraiaCommunity/graiax-text2img-playwright)
    """

    timeout: float | None
    type: Literal["jpeg", "png", None]
    quality: int | None
    omit_background: bool | None
    full_page: bool | None
    clip: FloatRect | None
    animations: Literal["allow", "disabled", None]
    caret: Literal["hide", "initial", None]
    scale: Literal["css", "device", None]
    mask: list[Locator] | None

class Text2ImgRender():
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None

    async def from_jinja_template(self, template: str, data: dict) -> str:
        html = Template(template).render(data)
        return await self.from_html(html)
    
    async def from_html(self, html: str) -> str:
        html_file_path, abs_path = generate_data_path(suffix="html", namespace="rendered")
        with open(html_file_path, "w", encoding='utf-8') as f:
            f.write(html)
        return html_file_path, abs_path
    
    async def html2pic(self, html_file_path: str, screenshot_options: ScreenshotOptions) -> str:
        if self.context is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch()
            self.context = await self.browser.new_context()
        result_path, _ = generate_data_path(suffix="jpeg", namespace="rendered")

        logging.info(f"Rendering {html_file_path}")

        page = await self.context.new_page()
        await page.goto(f'file://{html_file_path}')
        await page.screenshot(path=result_path, **screenshot_options)
        await page.close()

        logging.info(f"Rendered {html_file_path} to {result_path}")

        return result_path