from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import secrets
from models import APICall, APIKey, Base
import hashlib, secrets
    
from database import get_db, engine
print("DATABASE URL:", engine.url)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Optimizer", version="1.0")

# --- Exception Handlers ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    print(f"{request.method} {request.url.path} → {exc.status_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": [{"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()],
            "status_code": 422,
            "message": [e["msg"] for e in exc.errors()]
        }
    )

@app.exception_handler(SQLAlchemyError)
async def db_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "message": "A database error occurred"
        }
    )

# --- Pydantic Models ---

class APICallLog(BaseModel):
    provider: str
    model: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost: float = Field(ge=0)
    feature_name: Optional[str] = None
    timestamp: Optional[datetime] = None

class APICallResponse(BaseModel):
    id: int
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    feature_name: Optional[str] = None
    timestamp: datetime
    total_tokens: int

    class Config:
        from_attributes = True

class AlertRuleCreate(BaseModel):
    metric: str
    threshold: float = Field(gt=0)
    
# --- key function ---
def require_api_key(x_api_key: str = Header(...), db: Session = Depends(get_db)):
    db_key = db.query(APIKey).filter(
        APIKey.key == x_api_key,
        APIKey.is_active == True
    ).first()
    if db_key is None:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return db_key

# --- Routes ---
    
@app.get("/")
def home():
    return {"message": "Running"}

@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.0"}

@app.post("/log-call", response_model=APICallResponse)
def log_api_call(call: APICallLog, db: Session = Depends(get_db), _: APIKey = Depends(require_api_key)):
    resolved_timestamp = call.timestamp or datetime.now(timezone.utc)
    total = call.input_tokens + call.output_tokens

    db_call = APICall(
        provider=call.provider,
        model=call.model,
        input_tokens=call.input_tokens,
        output_tokens=call.output_tokens,
        cost=call.cost,
        feature_name=call.feature_name,
        timestamp=resolved_timestamp
    )

    db.add(db_call)
    db.commit()
    db.refresh(db_call)

    return APICallResponse(
        id=db_call.id,
        provider=db_call.provider,
        model=db_call.model,
        input_tokens=db_call.input_tokens,
        output_tokens=db_call.output_tokens,
        cost=db_call.cost,
        feature_name=db_call.feature_name,
        timestamp=db_call.timestamp,
        total_tokens=total
    )

@app.get("/logs")
def get_logs(limit: int = 10, offset: int = 0, sort_by:str="timestamp", db: Session = Depends(get_db), _: APIKey = Depends(require_api_key)
):
    column=getattr(APICall, sort_by, APICall.timestamp)
    logs = db.query(APICall).order_by(desc(column)).offset(offset).limit(limit).all()
    total = db.query(APICall).count()
    return {"total_calls": total, "limit": limit, "offset": offset, "logs": logs}

@app.get("/logs/summary")
def summary(db: Session = Depends(get_db), _: APIKey=Depends(require_api_key)):
    logs = db.query(APICall).all()
    total_tokens = 0
    total_cost = 0.0
    for item in logs:
        total_tokens += item.input_tokens + item.output_tokens
        total_cost += item.cost
    return {
        "total_calls": len(logs),
        "total_tokens": total_tokens,
        "total_cost": total_cost
    }

@app.post("/api-keys")
def create_api_key(name: str, db: Session = Depends(get_db)):
    raw_key = secrets.token_hex(32)   # 64-character random string
    db_key = APIKey(key=raw_key, name=name)
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return {"key": raw_key, "name": name, "id": db_key.id}

@app.get("/logs/filter")
def filter_logs(
    provider: Optional[str]=None,
    model: Optional[str]= None,
    start_date: Optional[datetime]= None,
    end_date: Optional[datetime]= None,
    db: Session= Depends(get_db),
    _: APIKey= Depends(require_api_key)
):  
    query= db.query(APICall)
    if provider:
        query=query.filter(APICall.provider == provider)
    if model:
        query=query.filter(APICall.model== model)
    if start_date:
        query=query.filter(APICall.timestamp>=start_date)
    if end_date:
        query= query.filter(APICall.timestamp<= end_date)
    logs=query.all()
    return {"total_calls": len(logs), "logs": logs}

@app.get("/logs/by-provider")
def logs_provider(db: Session=Depends(get_db), _: APIKey=Depends(require_api_key)):
    logs = db.query(APICall).all()
    breakdown={}
    for log in logs:
        if log.provider not in breakdown:
            breakdown[log.provider]={"total_calls":0, "total_cost":0, "total_tokens":0}
        breakdown[log.provider]["total_calls"]+=1
        breakdown[log.provider]["total_cost"]+=log.cost
        breakdown[log.provider]["total_tokens"]+=log.input_tokens+log.output_tokens
    return breakdown

@app.get('/logs/by-model')
def logs_by_model(db: Session=Depends(get_db), _:APIKey=Depends(require_api_key)):
    logs=db.query(APICall).all()
    breakdown={}
    for log in logs:
        if log.model not in breakdown:
            breakdown[log.model]= {"total_calls":0, "total_cost":0, "total_tokens":0}
        breakdown[log.model]["total_calls"]+=1
        breakdown[log.model]["total_cost"]+=log.cost
        breakdown[log.model]["total_tokens"]+=log.input_tokens+log.output_tokens
    return breakdown

@app.get("/logs/{log_id}")
def get_log(log_id: int, db: Session = Depends(get_db), _: APIKey = Depends(require_api_key)):
    log = db.query(APICall).filter(APICall.id == log_id).first()
    if log is None:
        raise HTTPException(status_code=404, detail="Log not found")
    return log

@app.get('/analysis/most_expensive_model')
def expensive_model(db: Session= Depends(get_db), _: APIKey=Depends(require_api_key)):
    logs=db.query(APICall).all()
    breakdown={}
    for log in logs:
        if log.model not in breakdown:
            breakdown[log.model]= {"total_cost": 0, "total_tokens": 0}
        breakdown[log.model]["total_cost"]+= log.cost
        breakdown[log.model]["total_tokens"]+= log.input_tokens+log.output_tokens

    for model in breakdown:
        total_cost= breakdown[model]["total_cost"]
        total_tokens= breakdown[model]["total_tokens"]
        breakdown[model]["expensive"]= total_tokens/total_cost

    highest= max(breakdown, key=lambda model: breakdown[model]["expensive"])
    return {
        "most_expensive_model": highest
    }

@app.get("/analysis/cost-breakdown")
def cost_breakdown(db: Session = Depends(get_db), _: APIKey = Depends(require_api_key)):
    logs = db.query(APICall).all()
    breakdown = {}
    for log in logs:
        if log.provider not in breakdown:
            breakdown[log.provider] = 0.0
        breakdown[log.provider] += log.cost
    return {"cost_by_provider": breakdown}

@app.get("/analysis/cost-by-feature")
def cost_by_feature(db: Session = Depends(get_db), _: APIKey = Depends(require_api_key)):
    logs = db.query(APICall).all()
    breakdown = {}
    for log in logs:
        feature = log.feature_name or "untagged"
        if feature not in breakdown:
            breakdown[feature] = {"total_calls": 0, "total_cost": 0.0, "total_tokens": 0}
        breakdown[feature]["total_calls"] += 1
        breakdown[feature]["total_cost"] += log.cost
        breakdown[feature]["total_tokens"] += log.input_tokens + log.output_tokens
    return breakdown

@app.get("/analysis/peak-hours")
def peak_hours(db: Session = Depends(get_db), _: APIKey = Depends(require_api_key)):
    logs = db.query(APICall).all()
    hours = {}
    for log in logs:
        hour = log.timestamp.hour
        if hour not in hours:
            hours[hour] = 0
        hours[hour] += 1
    sorted_hours = dict(sorted(hours.items(), key=lambda x: x[1], reverse=True))
    return {"peak_hours": sorted_hours}