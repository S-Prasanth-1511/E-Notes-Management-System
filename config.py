class Config:
    SECRET_KEY = 'irproj'  # Change this to a secure key
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/enotes'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
