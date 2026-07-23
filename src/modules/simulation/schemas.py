from pydantic import BaseModel


class SimulationLogResponse(BaseModel):
    log: str
