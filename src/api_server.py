import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import app

if __name__ == "__main__":
    import uvicorn
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("Dang khoi chay Enterprise Logistics Server (Modular Monolith) tai http://127.0.0.1:8000...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
