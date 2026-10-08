from app import create_app
import os
from config import Config

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', str(Config.PORT))), debug=Config.DEBUG)
