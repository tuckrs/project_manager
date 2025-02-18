# Create and activate virtual environment
python -m venv backend/venv
.\backend\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt

# Install frontend and electron dependencies
npm install
cd frontend
npm install
cd ..

# Build frontend
cd frontend
npm run build
cd ..

# Build electron application
npm run build
