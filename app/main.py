from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

sqlite_url = "sqlite:///./database.db"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


class Agent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "AgentBase is running!"}


@app.post("/agents/", response_model=Agent)
def create_agent(agent: Agent, session: SessionDep):
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent


@app.get("/agents/", response_model=list[Agent])
def read_agents(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    agents = session.exec(select(Agent).offset(offset).limit(limit)).all()
    return agents


@app.get("/agents/{agent_id}", response_model=Agent)
def read_agent(agent_id: int, session: SessionDep):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
