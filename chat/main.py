from fastapi import FastAPI, HTTPException,BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, Header
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from pydantic import BaseModel
import anthropic
from dotenv import load_dotenv
import os
import hmac
import hashlib
import secrets


app = FastAPI(docs_url=None, redoc_url=None)

load_dotenv()

ANTHROPIC_API= os.getenv("ANTHROPIC_API")

#for api end point security 
security=HTTPBasic()
CHAT_USERNAME=os.getenv("CHAT_USERNAME", "default_user")
CHAT_PASSWORD=os.getenv("CHAT_PASSWORD","default_password")
API_KEY=os.getenv("API_KEY", "apikey")
SECRET_KEY=os.getenv("SECRET_KEY")

#Configuration for CORS 

origins=[
    "https://nimble-gnome-f8228f.netlify.app/home",
    "http://localhost:5173",
    "https://api.akki.ai/run",
    "https://beta.akki.ai/",
    "https://beta.akki.ai"
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatInputs(BaseModel):
    MESSAGE: str
    HASH: str


async def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, CHAT_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, CHAT_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401, detail="Unauthorized", 
            headers={"WWW-Authenticate": "Basic"}
        )

#Function to authenticate api and secrets
async def authenticate_api_key(api_key: str = Header(None)):
    """
    Dependency to authenticate API Key and Secret.
    """
    if not (secrets.compare_digest(api_key or "", API_KEY)):
        raise HTTPException(status_code=403, detail="Unauthorized: Invalid API Key")

async def compute_hash(data: str,secret_key: str) ->str:
     """
     Computes hash with secret key at backend server with data received. Uses Hmac algorithm
     """
     return hmac.new(secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()

@app.post("/chat", dependencies= [Depends(authenticate_api_key)])
async def chat(input: ChatInputs, background_tasks: BackgroundTasks):
    try:
        message=input.MESSAGE
        received_hash= input.HASH

        if not (message and received_hash):
            raise HTTPException(status_code=400, detail="Invalid input data")
        
        data_string=f"{message}"
        #compute hash from data string
        computed_hash= await compute_hash(data_string,SECRET_KEY)

        # Validate the hash
        if not hmac.compare_digest(received_hash, computed_hash):
            raise HTTPException(status_code=401, detail="Unauthorized: Hash does not match")
        else: 
            if not ANTHROPIC_API:
                raise ValueError("ANTHROPIC_API environment variable not found. Please set it with your API key.")

            client= anthropic.Anthropic(api_key=ANTHROPIC_API)
            MODEL_NAME="claude-3-haiku-20240307"

            message = client.messages.create(
                model=MODEL_NAME,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": input.MESSAGE}
                ]
            )

            return {"response": message.content[0].text}
        
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/", dependencies=[Depends(authenticate)])
async def root():
    return {"message": "Welcome to the AkkiAI Chat"}

@app.get("/docs", dependencies=[Depends(authenticate)])
async def fastapi_docs():
    """
    Custom route for /docs to protect it with authentication.
    """
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="AkkiAI Chat"
    )