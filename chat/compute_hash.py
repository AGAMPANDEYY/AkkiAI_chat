import hmac
import hashlib
import os 
from dotenv import load_dotenv

load_dotenv()

message="string"

secret_key=os.getenv("SECRET_KEY")
#data=f"{solution_id}|{input1}|{input2}|{input3}"
data=f"{message}"

hash=hmac.new(secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()

print(hash)