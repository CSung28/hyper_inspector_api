from fastapi import FastAPI

from app.api.hyper_routes import router as hyper_router

app = FastAPI(
    title="Hyper Inspector API",
    version="0.1.0",
    description="Tableau .hyper 파일을 읽고 검사하는 API입니다.",
)

app.include_router(hyper_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
