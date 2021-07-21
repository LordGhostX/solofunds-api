from solofunds import app, db
from solofunds.models import *
from solofunds.routes import *

db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
