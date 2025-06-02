

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_USER = "fastapi_user"
DB_PASSWORD = "fastapi2024"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "NewSideDrop_dev"

# DATABASE_URL = f"mysql+mysqldb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@127.0.0.1:{DB_PORT}/{DB_NAME}"

DATABASE_URL = f"mysql+mysqldb://fastapi_user:fastapi2024@localhost:3306/NewSideDrop_dev"

print("🔧 Connecting with DB settings:")
print("  USER:", DB_USER)
print("  HOST:", DB_HOST)
print("  DB  :", DB_NAME)
print("  URL :", DATABASE_URL)
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


