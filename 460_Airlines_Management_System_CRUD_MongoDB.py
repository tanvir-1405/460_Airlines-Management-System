import customtkinter as ctk
from tkinter import ttk, messagebox
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# ------------------ MongoDB Connection ------------------
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["460_airlinesDB"]          # Database name
    collection = db["460_flights"]          # Collection name
except Exception as e:
    print("Error connecting to MongoDB:", e)
    exit()

# ------------------ Helpers ------------------
STATUS_CHOICES = ["Scheduled", "Delayed", "Cancelled", "Departed", "Arrived"]

def parse_dt(s: str):
    """
    Accept several common datetime formats and normalize to 'YYYY-MM-DD HH:MM'.
    Returns (ok: bool, normalized_or_msg: str)
    """
    s = s.strip()
    if not s:
        return False, "Empty date/time."
    fmts = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M",
        "%Y/%m/%d %H:%M",
        "%d %b %Y %H:%M",
        "%d %B %Y %H:%M",
        "%Y-%m-%dT%H:%M",
    ]
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            return True, dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    return False, "Use format like 2025-08-20 14:30"

def validate_inputs():
    flight_no = entry_flight_no.get().strip()
    airline = entry_airline.get().strip()
    origin = entry_origin.get().strip()
    destination = entry_destination.get().strip()
    dep_raw = entry_dep_time.get().strip()
    arr_raw = entry_arr_time.get().strip()
    status = status_var.get().strip()
    gate = entry_gate.get().strip()

    if not flight_no or not airline or not origin or not destination or not dep_raw or not arr_raw or not status or not gate:
        return False, "Please fill all fields."

    ok_dep, dep_norm = parse_dt(dep_raw)
    if not ok_dep:
        return False, f"Invalid Departure Date & Time. {dep_norm}"

    ok_arr, arr_norm = parse_dt(arr_raw)
    if not ok_arr:
        return False, f"Invalid Arrival Date & Time. {arr_norm}"

    data = {
        "flight_no": flight_no,
        "airline": airline,
        "origin": origin,
        "destination": destination,
        "departure": dep_norm,
        "arrival": arr_norm,
        "status": status,
        "gate": gate
    }
    return True, data

# ------------------ CRUD Functions ------------------
def insert_data():
    ok, payload = validate_inputs()
    if not ok:
        messagebox.showwarning("Input Error", payload)
        return
    try:
        collection.insert_one(payload)
        messagebox.showinfo("Success", "Flight record inserted successfully!")
        clear_fields()
        fetch_data()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def fetch_data():
    for row in tree.get_children():
        tree.delete(row)
    try:
        for doc in collection.find().sort("_id", 1):  # Show oldest first
            tree.insert(
                "",
                "end",
                iid=str(doc["_id"]),
                values=(
                    doc.get("flight_no", ""),
                    doc.get("airline", ""),
                    doc.get("origin", ""),
                    doc.get("destination", ""),
                    doc.get("departure", ""),
                    doc.get("arrival", ""),
                    doc.get("status", ""),
                    doc.get("gate", ""),
                ),
            )
    except Exception as e:
        messagebox.showerror("Error", str(e))

def update_data():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select a record to update.")
        return

    ok, payload = validate_inputs()
    if not ok:
        messagebox.showwarning("Input Error", payload)
        return

    record_id = ObjectId(selected[0])
    try:
        collection.update_one({"_id": record_id}, {"$set": payload})
        messagebox.showinfo("Success", "Flight record updated successfully!")
        clear_fields()
        fetch_data()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def delete_data():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select a record to delete.")
        return

    record_id = ObjectId(selected[0])
    confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?")
    if confirm:
        try:
            collection.delete_one({"_id": record_id})
            messagebox.showinfo("Success", "Flight record deleted successfully!")
            fetch_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))

def clear_fields():
    entry_flight_no.delete(0, "end")
    entry_airline.delete(0, "end")
    entry_origin.delete(0, "end")
    entry_destination.delete(0, "end")
    entry_dep_time.delete(0, "end")
    entry_arr_time.delete(0, "end")
    status_var.set(STATUS_CHOICES[0])
    entry_gate.delete(0, "end")

def select_record(event):
    selected = tree.selection()
    if selected:
        record = collection.find_one({"_id": ObjectId(selected[0])})
        if record:
            clear_fields()
            entry_flight_no.insert(0, record.get("flight_no", ""))
            entry_airline.insert(0, record.get("airline", ""))
            entry_origin.insert(0, record.get("origin", ""))
            entry_destination.insert(0, record.get("destination", ""))
            entry_dep_time.insert(0, record.get("departure", ""))
            entry_arr_time.insert(0, record.get("arrival", ""))
            status_var.set(record.get("status", STATUS_CHOICES[0]))
            entry_gate.insert(0, record.get("gate", ""))

# ------------------ CustomTkinter Setup ------------------
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("✈️ Flight Management System")
root.geometry("980x620")  # Slightly wider to fit 8 fields comfortably

# Title
title_label = ctk.CTkLabel(root, text="✈️ Flight Management System", font=ctk.CTkFont(size=22, weight="bold"))
title_label.pack(pady=15)

# Form Frame
form_frame = ctk.CTkFrame(root)
form_frame.pack(pady=10, padx=20, fill="x")

# ---- Row 1 ----
entry_flight_no = ctk.CTkEntry(form_frame, placeholder_text="Flight Number (e.g., AI203)", width=200)
entry_flight_no.grid(row=0, column=0, padx=10, pady=10)

entry_airline = ctk.CTkEntry(form_frame, placeholder_text="Airline Name", width=200)
entry_airline.grid(row=0, column=1, padx=10, pady=10)

entry_origin = ctk.CTkEntry(form_frame, placeholder_text="Origin (City/Airport)", width=200)
entry_origin.grid(row=0, column=2, padx=10, pady=10)

entry_destination = ctk.CTkEntry(form_frame, placeholder_text="Destination (City/Airport)", width=200)
entry_destination.grid(row=0, column=3, padx=10, pady=10)

# ---- Row 2 ----
entry_dep_time = ctk.CTkEntry(form_frame, placeholder_text="Departure (YYYY-MM-DD HH:MM)", width=220)
entry_dep_time.grid(row=1, column=0, padx=10, pady=10)

entry_arr_time = ctk.CTkEntry(form_frame, placeholder_text="Arrival (YYYY-MM-DD HH:MM)", width=220)
entry_arr_time.grid(row=1, column=1, padx=10, pady=10)

status_var = ctk.StringVar(value=STATUS_CHOICES[0])
status_menu = ctk.CTkOptionMenu(form_frame, variable=status_var, values=STATUS_CHOICES, width=180)
status_menu.grid(row=1, column=2, padx=10, pady=10)
status_menu.set(STATUS_CHOICES[0])

entry_gate = ctk.CTkEntry(form_frame, placeholder_text="Gate / Terminal (e.g., T3-G12)", width=200)
entry_gate.grid(row=1, column=3, padx=10, pady=10)

# Buttons
btn_frame = ctk.CTkFrame(root)
btn_frame.pack(pady=5)

ctk.CTkButton(btn_frame, text="Add", command=insert_data, fg_color="green").grid(row=0, column=0, padx=10, pady=5)
ctk.CTkButton(btn_frame, text="Update", command=update_data, fg_color="blue").grid(row=0, column=1, padx=10, pady=5)
ctk.CTkButton(btn_frame, text="Delete", command=delete_data, fg_color="red").grid(row=0, column=2, padx=10, pady=5)
ctk.CTkButton(btn_frame, text="Read", command=fetch_data, fg_color="orange").grid(row=0, column=3, padx=10, pady=5)
ctk.CTkButton(btn_frame, text="Clear", command=clear_fields, fg_color="gray").grid(row=0, column=4, padx=10, pady=5)

# Table
tree_frame = ctk.CTkFrame(root)
tree_frame.pack(pady=10, padx=20, fill="both", expand=True)

columns = ("Flight No", "Airline", "Origin", "Destination", "Departure", "Arrival", "Status", "Gate/Terminal")
tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)

for col in columns:
    tree.heading(col, text=col)

# Reasonable widths
tree.column("Flight No", anchor="center", width=100)
tree.column("Airline", anchor="center", width=130)
tree.column("Origin", anchor="center", width=120)
tree.column("Destination", anchor="center", width=130)
tree.column("Departure", anchor="center", width=160)
tree.column("Arrival", anchor="center", width=160)
tree.column("Status", anchor="center", width=110)
tree.column("Gate/Terminal", anchor="center", width=120)

tree.pack(fill="both", expand=True)
tree.bind("<<TreeviewSelect>>", select_record)

# Fetch initial data
fetch_data()

root.mainloop()
