import asyncio

from fastapi import FastAPI

from process_service.src.main import lifespan


def test_lifespan_sets_manager():
    app = FastAPI()
    async_gen = lifespan(app)

    async def run_lifespan():
        await async_gen.__anext__()
        assert hasattr(app.state, "manager")
        await async_gen.asend(None)

    asyncio.run(run_lifespan())
