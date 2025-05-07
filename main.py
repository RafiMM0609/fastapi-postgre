from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sentry_sdk
from settings import (
    CORS_ALLOWED_ORIGINS,
    SENTRY_DSN,
    SENTRY_TRACES_SAMPLE_RATES,
    FILE_STORAGE_ADAPTER,
    ENVIRONTMENT
)
from core.logging_config import logger
from routes.auth import router as auth_router
from routes.rbac import router as rbac_router
from fastapi.responses import HTMLResponse


if SENTRY_DSN != None:  # NOQA
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATES,
    )

# END OF INISIALISASI CRONJOB
    # --- shutdown ---
# Inisialisasi FastAPI berdasarkan ENVIRONTMENT
fastapi_kwargs = {
    "title": "Telkom AI",
    "swagger_ui_oauth2_redirect_url": "/docs/oauth2-redirect",
    "swagger_ui_init_oauth": {
        "clientId": "your-client-id",
        "authorizationUrl": "/auth/token",
        "tokenUrl": "/auth/token",
    },
}
if ENVIRONTMENT == 'dev':
    fastapi_kwargs.update({
        "docs_url": "/docs",
        "redoc_url": None,
        "openapi_url": "/openapi.json",
    })
elif ENVIRONTMENT == 'prod':
    fastapi_kwargs.update({
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    })
app = FastAPI(**fastapi_kwargs)

app.add_middleware(
    CORSMiddleware,
    # allow_origins=CORS_ALLOWED_ORIGINS,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if FILE_STORAGE_ADAPTER != 'minio':
    app.mount("/static", StaticFiles(directory="static"))



app.include_router(auth_router, prefix="/auth")
app.include_router(rbac_router, prefix="/rbac")



@app.get("/")
async def hello():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Telkom AI dashboard</title>
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #fff;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                background: rgba(0,0,0,0.3);
                padding: 40px 60px;
                border-radius: 16px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                text-align: center;
            }
            h1 {
                margin-bottom: 10px;
                font-size: 2.5rem;
                letter-spacing: 2px;
            }
            p {
                font-size: 1.2rem;
                margin-top: 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>👋 Welcome to Our Backend Service API</h1>
            <p>FastAPI + PostgreSQL + Sentry + CORS</p>
            <p>Happy Code</p>
            <p>Bismillah bro</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


