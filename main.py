from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import time

app = FastAPI(title="Coffee Shop API", docs_url="/docs")

# Модели данных
class MenuItemBase(BaseModel):
    name: str = Field(..., min_length=1, description="Название позиции")
    price: float = Field(..., gt=0, description="Цена должна быть больше 0")
    category: Optional[str] = "general"

class MenuItemCreate(MenuItemBase):
    pass

class MenuItem(MenuItemBase):
    id: int

# "База данных" в памяти
db: List[MenuItem] = []
next_id = 1

# Middleware для логирования (★★)
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    print(f"{request.method} {request.url.path} {response.status_code} {process_time:.1f}ms")
    return response

# GET /health
@app.get("/health")
def health_check():
    return {"status": "ok"}

# POST /api/menu_items (создание)
@app.post("/api/menu_items", status_code=201, response_model=MenuItem)
def create_item(item: MenuItemCreate):
    global next_id
    new_item = MenuItem(id=next_id, **item.dict())
    db.append(new_item)
    next_id += 1
    return new_item

# GET /api/menu_items (список с пагинацией и фильтром ★)
@app.get("/api/menu_items", response_model=List[MenuItem])
def get_items(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None
):
    result = db
    if category:
        result = [i for i in result if i.category == category]
    return result[offset : offset + limit]

# GET /api/menu_items/{id}
@app.get("/api/menu_items/{item_id}", response_model=MenuItem)
def get_item(item_id: int):
    for item in db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

# PUT /api/menu_items/{id} (обновление)
@app.put("/api/menu_items/{item_id}", response_model=MenuItem)
def update_item(item_id: int, item: MenuItemCreate):
    for index, existing_item in enumerate(db):
        if existing_item.id == item_id:
            updated_item = MenuItem(id=item_id, **item.dict())
            db[index] = updated_item
            return updated_item
    raise HTTPException(status_code=404, detail="Item not found")

# DELETE /api/menu_items/{id} (удаление)
@app.delete("/api/menu_items/{item_id}", status_code=204)
def delete_item(item_id: int):
    for index, item in enumerate(db):
        if item.id == item_id:
            del db[index]
            return
    raise HTTPException(status_code=404, detail="Item not found")