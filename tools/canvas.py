from pydantic import BaseModel, Field
from typing import Literal, Optional
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import markdown
import os

class CanvasInput(BaseModel):
    format: Literal["text", "report", "summary", "code"] = Field(..., description="The template type to use.")
    title: str = Field(..., description="Title of the document.")
    body: str = Field(..., description="The main content in Markdown format.")
    language: Optional[str] = Field(None, description="Programming language if format is 'code'.")


def canvas_tool(data: CanvasInput):
    """
    Renders the final result into a structured document (Canvas).
    """
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('canvas_base.html')

    html_output = template.render(
        title=data.title,
        body=data.body,
        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        format=data.format
    )

    return html_output


