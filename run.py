# Import the create_app function from the app package
from app import create_app

# Create an instance of the Flask application
app = create_app()

# Run the application in debug mode if this file is executed directly
if __name__ == '__main__':
    app.run(debug=True)
