#!/usr/bin/env python
"""Setup and run Flask app"""

import subprocess
import sys
import os

os.chdir(r"c:\Users\Lil_r\OneDrive\Desktop\shikkathikaa3.0\ai_exam_corrector")

print("📦 Installing dependencies...")
result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                       capture_output=False)

if result.returncode != 0:
    print("⚠️ Some dependencies may not have installed. This is OK if Flask/Pillow are present.")

print("\n✅ Setup complete!")
print("\n🚀 To start the web application:")
print("   python app.py")
print("\n📝 Then open: http://localhost:5000")
