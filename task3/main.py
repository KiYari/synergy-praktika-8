from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import asyncpg
import os

class ProblemCreate(BaseModel):
    user_description: str
    category: str

class SymptomCreate(BaseModel):
    type: str
    value: str
    environment: Optional[str] = None

class ActionCreate(BaseModel):
    action_taken: str
    result: str
    performed_by: str

class SolutionCreate(BaseModel):
    description: str
    steps: str
    confidence: float
    for_line: str

class CauseCreate(BaseModel):
    cause_description: str
    confidence: float

app = FastAPI(title="Expert System Support", version="1.0.0")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

async def get_db_connection():
    conn = await asyncpg.connect(
        user="your_username",
        password="your_password",
        database="your_database",
        host="localhost"
    )
    try:
        yield conn
    finally:
        await conn.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, conn=Depends(get_db_connection)):
    problems = await conn.fetch("""
        SELECT p.*,
               COUNT(DISTINCT s.symptom_id) as symptom_count,
               COUNT(DISTINCT a.action_id) as action_count,
               COUNT(DISTINCT sol.solution_id) as solution_count
        FROM problems p
        LEFT JOIN symptoms s ON p.issue_id = s.issue_id
        LEFT JOIN actions a ON p.issue_id = a.issue_id
        LEFT JOIN solutions sol ON p.issue_id = sol.issue_id
        GROUP BY p.issue_id
        ORDER BY p.created_at DESC
    """)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "problems": [dict(problem) for problem in problems]
    })

@app.get("/problems/new", response_class=HTMLResponse)
async def new_problem_form(request: Request):
    categories = ["network", "software", "hardware", "access", "performance", "security"]
    return templates.TemplateResponse("problem_form.html", {
        "request": request,
        "categories": categories
    })

@app.post("/problems/create", response_class=RedirectResponse)
async def create_problem_from_form(
    user_description: str = Form(...),
    category: str = Form(...),
    conn=Depends(get_db_connection)
):
    issue_id = f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    await conn.execute(
        "INSERT INTO problems (issue_id, user_description, category) VALUES ($1, $2, $3)",
        issue_id, user_description, category
    )

    return RedirectResponse(url=f"/problems/{issue_id}", status_code=303)

@app.get("/problems/{issue_id}", response_class=HTMLResponse)
async def problem_detail(request: Request, issue_id: str, conn=Depends(get_db_connection)):
    problem = await conn.fetchrow("SELECT * FROM problems WHERE issue_id = $1", issue_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    symptoms = await conn.fetch("SELECT * FROM symptoms WHERE issue_id = $1 ORDER BY created_at", issue_id)
    actions = await conn.fetch("SELECT * FROM actions WHERE issue_id = $1 ORDER BY created_at", issue_id)
    solutions = await conn.fetch("SELECT * FROM solutions WHERE issue_id = $1 ORDER BY confidence DESC", issue_id)
    causes = await conn.fetch("SELECT * FROM possible_causes WHERE issue_id = $1 ORDER BY confidence DESC", issue_id)

    symptom_types = ["error_message", "performance_issue", "login_failure", "connection_problem", "hardware_failure", "software_crash", "access_denied"]
    action_types = ["reboot", "reinstall", "cleared_cache", "checked_cable", "updated_drivers", "reset_password", "changed_settings"]
    result_types = ["success", "failure", "no_change"]
    line_types = ["line_1", "line_2"]

    return templates.TemplateResponse("problem_detail.html", {
        "request": request,
        "problem": dict(problem),
        "symptoms": [dict(symptom) for symptom in symptoms],
        "actions": [dict(action) for action in actions],
        "solutions": [dict(solution) for solution in solutions],
        "causes": [dict(cause) for cause in causes],
        "symptom_types": symptom_types,
        "action_types": action_types,
        "result_types": result_types,
        "line_types": line_types
    })

@app.post("/problems/{issue_id}/symptoms/add", response_class=RedirectResponse)
async def add_symptom_from_form(
    issue_id: str,
    type: str = Form(...),
    value: str = Form(...),
    environment: str = Form(None),
    conn=Depends(get_db_connection)
):
    await conn.execute(
        "INSERT INTO symptoms (issue_id, type, value, environment) VALUES ($1, $2, $3, $4)",
        issue_id, type, value, environment
    )
    return RedirectResponse(url=f"/problems/{issue_id}#symptoms", status_code=303)

@app.post("/problems/{issue_id}/actions/add", response_class=RedirectResponse)
async def add_action_from_form(
    issue_id: str,
    action_taken: str = Form(...),
    result: str = Form(...),
    performed_by: str = Form(...),
    conn=Depends(get_db_connection)
):
    await conn.execute(
        "INSERT INTO actions (issue_id, action_taken, result, performed_by) VALUES ($1, $2, $3, $4)",
        issue_id, action_taken, result, performed_by
    )
    return RedirectResponse(url=f"/problems/{issue_id}#actions", status_code=303)

@app.post("/problems/{issue_id}/solutions/add", response_class=RedirectResponse)
async def add_solution_from_form(
    issue_id: str,
    description: str = Form(...),
    steps: str = Form(...),
    confidence: float = Form(...),
    for_line: str = Form(...),
    conn=Depends(get_db_connection)
):
    solution_id = f"SOL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    await conn.execute(
        "INSERT INTO solutions (solution_id, issue_id, description, steps, confidence, for_line) VALUES ($1, $2, $3, $4, $5, $6)",
        solution_id, issue_id, description, steps, confidence, for_line
    )
    return RedirectResponse(url=f"/problems/{issue_id}#solutions", status_code=303)

@app.post("/problems/{issue_id}/causes/add", response_class=RedirectResponse)
async def add_cause_from_form(
    issue_id: str,
    cause_description: str = Form(...),
    confidence: float = Form(...),
    conn=Depends(get_db_connection)
):
    await conn.execute(
        "INSERT INTO possible_causes (issue_id, cause_description, confidence) VALUES ($1, $2, $3)",
        issue_id, cause_description, confidence
    )
    return RedirectResponse(url=f"/problems/{issue_id}#causes", status_code=303)

@app.post("/solutions/{solution_id}/apply", response_class=RedirectResponse)
async def apply_solution_from_form(
    solution_id: str,
    result: str = Form(...),
    conn=Depends(get_db_connection)
):
    solution = await conn.fetchrow("SELECT * FROM solutions WHERE solution_id = $1", solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    issue_id = solution['issue_id']

    await conn.execute(
        "UPDATE solutions SET is_applied = TRUE, applied_at = $1, result = $2 WHERE solution_id = $3",
        datetime.now(), result, solution_id
    )

    return RedirectResponse(url=f"/problems/{issue_id}#solutions", status_code=303)

@app.get("/search", response_class=HTMLResponse)
async def search_problems(
    request: Request,
    category: str = None,
    status: str = None,
    conn=Depends(get_db_connection)
):
    query = """
        SELECT p.*,
               COUNT(DISTINCT s.symptom_id) as symptom_count,
               COUNT(DISTINCT a.action_id) as action_count,
               COUNT(DISTINCT sol.solution_id) as solution_count
        FROM problems p
        LEFT JOIN symptoms s ON p.issue_id = s.issue_id
        LEFT JOIN actions a ON p.issue_id = a.issue_id
        LEFT JOIN solutions sol ON p.issue_id = sol.issue_id
        WHERE 1=1
    """
    params = []

    if category:
        query += " AND p.category = $1"
        params.append(category)

    if status:
        if len(params) == 0:
            query += " AND p.status = $1"
        else:
            query += " AND p.status = $2"
        params.append(status)

    query += " GROUP BY p.issue_id ORDER BY p.created_at DESC"

    problems = await conn.fetch(query, *params)

    categories = ["network", "software", "hardware", "access", "performance", "security"]
    statuses = ["new", "in_progress", "resolved", "closed"]

    return templates.TemplateResponse("search.html", {
        "request": request,
        "problems": [dict(problem) for problem in problems],
        "categories": categories,
        "statuses": statuses,
        "selected_category": category,
        "selected_status": status
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)