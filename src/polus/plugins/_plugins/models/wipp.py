from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field

from ..io import Input, Output, Version
from .WIPPPluginSchema import UiItem, WippPluginManifest  # type: ignore


class ui1(BaseModel):
    key: str = Field(constr=r"^inputs.[a-zA-Z0-9][-a-zA-Z0-9]*$")
    title: str
    description: Optional[str]
    condition: Optional[str]
    default: Optional[Union[str, float, int, bool]]
    hidden: Optional[bool] = Field(default=False)
    bind: Optional[str]


class FieldSet(BaseModel):
    title: str
    fields: List[str] = Field(min_items=1, unique_items=True)


class ui2(BaseModel):
    key: Literal["fieldsets"]
    fieldsets: List[FieldSet] = Field(min_items=1, unique_items=True)


class WIPPPluginManifest(WippPluginManifest):
    inputs: List[Input] = Field(
        ..., description="Defines inputs to the plugin", title="List of Inputs"
    )
    outputs: List[Output] = Field(
        ..., description="Defines the outputs of the plugin", title="List of Outputs"
    )
    ui: List[Union[ui1, ui2]] = Field(..., title="Plugin form UI definition")
    version: Version