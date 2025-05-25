# SplitWiseRepo
Step 1:
# Create the virtual enviornment then activate it
  python3 -m venv venv        # Create virtual environment named 'venv'
  source venv/bin/activate    # Activate it
Step 2:
# Install all the requirements
  pip3 install requirements.txt
# Run the app with the help of following command 
  python3 -m uvicorn main:app --reload --port 8080
This command will create all the necessary tables in the database and complete the setup process 




