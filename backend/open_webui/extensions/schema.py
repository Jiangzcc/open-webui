from pydantic import BaseModel, ConfigDict


class StrictFrozenModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


__all__ = ['StrictFrozenModel']
