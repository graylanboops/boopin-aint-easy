import os
import sqlite3
import logging
import httpx
import numpy as np
import tkinter as tk
import tkinter.simpledialog as simpledialog
import psutil
import time
import asyncio
import threading
from tkinter import filedialog
import pennylane as qml
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO)

def generate_key():
    return Fernet.generate_key()

def load_key():
    key_path = os.path.expanduser("~/.cache/encryption.key")
    if os.path.exists(key_path):
        with open(key_path, "rb") as key_file:
            return key_file.read()
    else:
        key = generate_key()
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        with open(key_path, "wb") as key_file:
            key_file.write(key)
        return key

def save_encrypted_key(api_key):
    key = load_key()
    fernet = Fernet(key)
    encrypted_key = fernet.encrypt(api_key.encode())
    with open(os.path.expanduser("~/.cache/encrypted_api_key.bin"), "wb") as file:
        file.write(encrypted_key)

def load_decrypted_key():
    key = load_key()
    fernet = Fernet(key)
    with open(os.path.expanduser("~/.cache/encrypted_api_key.bin"), "rb") as file:
        encrypted_key = file.read()
    return fernet.decrypt(encrypted_key).decode()

async def run_openai_completion(prompt, openai_api_key):
    retries = 3
    timeout = 10
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(retries):
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_api_key}"
                }
                data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=data,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                completion = result["choices"][0]["message"]["content"]
                return completion.strip()
            except Exception:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return None

def get_cpu_ram_usage():
    try:
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        return cpu_usage, ram_usage
    except Exception:
        return None, None

def quantum_risk_analysis(cpu_usage, ram_usage):
    try:
        cpu_param = cpu_usage / 100
        ram_param = ram_usage / 100

        dev = qml.device("default.qubit", wires=5)

        @qml.qnode(dev)
        def circuit(cpu_param, ram_param):
            qml.RY(np.pi * cpu_param, wires=0)
            qml.RY(np.pi * ram_param, wires=1)
            qml.CNOT(wires=[0, 1])
            qml.RY(np.pi * (cpu_param + 0.5), wires=2)
            qml.CNOT(wires=[1, 2])
            qml.RY(np.pi * (ram_param + 0.5), wires=3)
            qml.CNOT(wires=[2, 3])
            qml.RY(np.pi * (cpu_param + ram_param), wires=4)
            qml.CNOT(wires=[3, 4])
            return qml.probs(wires=[0, 1, 2, 3, 4])

        return circuit(cpu_param, ram_param)
    except Exception:
        return None

class QuantumRiskScanner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quantum Risk Scanner")
        self.geometry("700x900")

        font_large = ("Helvetica", 14)

        self.scan_scope_label = tk.Label(self, text="Enter the scope of your risk scan:", font=font_large)
        self.scan_scope_label.pack()

        self.scan_scope_entry = tk.Entry(self, width=40, font=font_large)
        self.scan_scope_entry.pack()

        self.risk_threshold_label = tk.Label(self, text="Risk Sensitivity Level (1-10):", font=font_large)
        self.risk_threshold_label.pack()

        self.risk_threshold_entry = tk.Entry(self, width=40, font=font_large)
        self.risk_threshold_entry.pack()

        self.start_button = tk.Button(self, text="Start Quantum Risk Scan", font=font_large, command=self.start_thread)
        self.start_button.pack()

        self.result_text = tk.Text(self, width=70, height=40, font=font_large)
        self.result_text.pack()

        self.settings_menu = tk.Menu(self)
        self.settings_menu.add_command(label="Settings", command=self.open_settings)
        self.config(menu=self.settings_menu)

        self.setup_database()

    def setup_database(self):
        try:
            db = sqlite3.connect('risk_scanner.db')
            cursor = db.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS risk_reports (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                prompt TEXT NOT NULL,
                                completion TEXT NOT NULL
                            )''')
            db.commit()
        finally:
            db.close()

    def open_settings(self):
        api_key = simpledialog.askstring("API Key", "Enter your OpenAI API Key:", show='*')
        if api_key:
            save_encrypted_key(api_key)

    def start_thread(self):
        threading.Thread(target=self.start, daemon=True).start()

    def start(self):
        scan_scope = self.scan_scope_entry.get()
        risk_level = self.risk_threshold_entry.get()
        try:
            openai_api_key = load_decrypted_key()
        except:
            return

        try:
            db = sqlite3.connect('risk_scanner.db')
            with db:
                cursor = db.cursor()
                cpu_usage, ram_usage = get_cpu_ram_usage()
                if cpu_usage is not None and ram_usage is not None:
                    self.result_text.insert(tk.END, f"CPU usage: {cpu_usage}%\n")
                    self.result_text.insert(tk.END, f"RAM usage: {ram_usage}%\n")
                    self.result_text.update_idletasks()

                quantum_results = quantum_risk_analysis(cpu_usage, ram_usage)
                self.result_text.insert(tk.END, f"Quantum Circuit Result: {quantum_results}\n")
                self.result_text.update_idletasks()

                prompt = f"""
                [action] Risk Assessment Request [/action]
                Perform a comprehensive quantum-enhanced risk analysis based on the following:

                - Scope of Scan: {scan_scope}
                - Risk Sensitivity Level: {risk_level}
                - CPU Usage: {cpu_usage}%
                - RAM Usage: {ram_usage}%
                - Quantum State: {quantum_results}

                Deliver:
                - Identified Threats and Vulnerabilities
                - Recommended Derisking Actions
                - Risk Score and Justification
                - Quantum Insight Analysis

                [action] End Request [/action]
                """

                result = asyncio.run(run_openai_completion(prompt, openai_api_key))
                if result:
                    self.result_text.insert(tk.END, f"\nQuantum Risk Analysis Result:\n{result}\n")
                else:
                    self.result_text.insert(tk.END, "\nFailed to retrieve AI response.\n")
                self.result_text.update_idletasks()

                cursor.execute("INSERT INTO risk_reports (prompt, completion) VALUES (?, ?)", (prompt, result))
                db.commit()

        finally:
            db.close()

if __name__ == "__main__":
    app = QuantumRiskScanner()
    app.mainloop()
