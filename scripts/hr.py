import gradio as gr
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import httpx
from threading import Thread

# Sample data
employees = {
    "101": {"name": "Alice Johnson", "position": "Manager", "salary": 60000, "performance": "Excellent"},
    "102": {"name": "Bob Smith", "position": "Developer", "salary": 50000, "performance": "Good"},
}

app = FastAPI()

# Pydantic models
class Employee(BaseModel):
    name: str
    position: str
    salary: int
    performance: str

class UpdatePerformance(BaseModel):
    performance: str

# FastAPI endpoints
@app.post("/add_employee/")
async def add_employee(emp_id: str, employee: Employee):
    if emp_id in employees:
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    employees[emp_id] = employee.dict()
    return {"message": f"Employee {employee.name} added successfully!"}

@app.get("/view_employee/{emp_id}")
async def view_employee(emp_id: str):
    if emp_id in employees:
        return employees[emp_id]
    raise HTTPException(status_code=404, detail="Employee not found")

@app.put("/update_performance/{emp_id}")
async def update_performance(emp_id: str, update: UpdatePerformance):
    if emp_id in employees:
        employees[emp_id]['performance'] = update.performance
        return {"message": f"Performance for Employee ID {emp_id} updated to {update.performance}"}
    raise HTTPException(status_code=404, detail="Employee not found")

@app.get("/calculate_payroll/")
async def calculate_payroll():
    payroll_info = ""
    total_payroll = 0
    for emp_id, emp in employees.items():
        payroll_info += f"ID: {emp_id}, Name: {emp['name']}, Salary: {emp['salary']}\n"
        total_payroll += emp['salary']
    payroll_info += f"\nTotal Payroll: {total_payroll}"
    return {"payroll": payroll_info}

# Gradio functions
def gr_add_employee(emp_id, name, position, salary, performance):
    response = httpx.post(f"http://127.0.0.1:8000/add_employee/?emp_id={emp_id}", json={
        "name": name, "position": position, "salary": salary, "performance": performance
    })
    return response.json().get("message", response.json().get("detail"))

def gr_view_employee(emp_id):
    response = httpx.get(f"http://127.0.0.1:8000/view_employee/{emp_id}")
    if response.status_code == 200:
        emp = response.json()
        return f"ID: {emp_id}\nName: {emp['name']}\nPosition: {emp['position']}\nSalary: {emp['salary']}\nPerformance: {emp['performance']}"
    return response.json().get("detail")

def gr_update_performance(emp_id, performance):
    response = httpx.put(f"http://127.0.0.1:8000/update_performance/{emp_id}", json={"performance": performance})
    return response.json().get("message", response.json().get("detail"))

def gr_calculate_payroll():
    response = httpx.get("http://127.0.0.1:8000/calculate_payroll/")
    return response.json().get("payroll")

# Gradio interface
def run_gradio_interface():
    with gr.Blocks() as hr_tool:
        gr.Markdown("# Non-Profit HR Management Tool")

        with gr.Tab("Add Employee"):
            emp_id = gr.Textbox(label="Employee ID")
            name = gr.Textbox(label="Name")
            position = gr.Textbox(label="Position")
            salary = gr.Number(label="Salary")
            performance = gr.Dropdown(["Excellent", "Good", "Average", "Poor"], label="Performance")
            add_button = gr.Button("Add Employee")
            add_result = gr.Textbox(label="Result")
            add_button.click(gr_add_employee, inputs=[emp_id, name, position, salary, performance], outputs=add_result)

        with gr.Tab("View Employee"):
            emp_id_view = gr.Textbox(label="Employee ID")
            view_button = gr.Button("View Employee")
            view_result = gr.Textbox(label="Employee Details")
            view_button.click(gr_view_employee, inputs=emp_id_view, outputs=view_result)

        with gr.Tab("Update Performance"):
            emp_id_update = gr.Textbox(label="Employee ID")
            performance_update = gr.Dropdown(["Excellent", "Good", "Average", "Poor"], label="Performance")
            update_button = gr.Button("Update Performance")
            update_result = gr.Textbox(label="Result")
            update_button.click(gr_update_performance, inputs=[emp_id_update, performance_update], outputs=update_result)

        with gr.Tab("Calculate Payroll"):
            payroll_button = gr.Button("Calculate Payroll")
            payroll_result = gr.Textbox(label="Payroll Details")
            payroll_button.click(gr_calculate_payroll, outputs=payroll_result)

    hr_tool.launch()

# Run FastAPI and Gradio concurrently
def run_fastapi():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    # Start the FastAPI server in a separate thread
    api_thread = Thread(target=run_fastapi)
    api_thread.start()

    # Start the Gradio interface
    run_gradio_interface()
