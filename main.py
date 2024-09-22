from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from io import StringIO
import csv
import os

app = FastAPI()


DATA_DIR = "transaction_data"
#create a new directory if it does not exist
os.makedirs(DATA_DIR, exist_ok=True)

@app.post("/transactions")
async def add_transactions(
    file: UploadFile = File(...), 
    name: str = Form(...), 
    keep_previous_records: bool = Form(True)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")


    content = await file.read()
    content = content.decode('utf-8') 
    csv_reader = csv.reader(StringIO(content))

    user_file_path = os.path.join(DATA_DIR, f"{name}_transactions.csv")

    # Assumptions each user can add csv file that can be added up together to give final report or user can add new csv file to replace all the old one
    if not keep_previous_records and os.path.exists(user_file_path):
        open(user_file_path, "w").close()  # Empty the file if user wants to overwrite

    try:
        with open(user_file_path, "a") as user_file:
            writer = csv.writer(user_file)

            for row in csv_reader:
                # Skip comments and malformed rows
                if len(row) == 0 or row[0].startswith("#"):
                    continue

                if len(row) != 4:
                    continue

                print(row)
                date, type_, amount, memo = row
                amount = float(amount) 

                # Write to the user's file
                writer.writerow([date, type_, amount, memo])

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")

    return {"message": "Transactions added successfully"}

@app.get("/report")
def generate_report(name: str):
    user_file_path = os.path.join(DATA_DIR, f"{name}_transactions.csv")

    if not os.path.exists(user_file_path):
        raise HTTPException(status_code=404, detail="No transactions found for the user")

    total_income = 0.0
    total_expense = 0.0

    with open(user_file_path, "r") as user_file:
        csv_reader = csv.reader(user_file)

        for row in csv_reader:
            date, type_, amount, memo = row
            amount = float(amount)

            if type_.strip().lower() == "income":
                total_income += amount
            elif type_.strip().lower() == "expense":
                total_expense += amount

    net_revenue = total_income - total_expense

    return {
        'gross-revenue': round(total_income, 2),
        'expenses': round(total_expense, 2),
        'net-revenue': round(net_revenue, 2)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
