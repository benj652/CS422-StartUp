'''
.env secret names
'''
SECRET_KEY = "SECRET_KEY"
SQLALCHEMY_DATABASE_URI = "SQLALCHEMY_DATABASE_URI"
SQLALCHEMY_TRACK_MODIFICATIONS = "SQLALCHEMY_TRACK_MODIFICATIONS"

'''
fallbacks
'''
FALLBACK_SECRET_KEY = "dev"
FALLBACK_SQLALCHEMY_DATABASE_URI = "sqlite:///testing.db"

'''
Deployment variables
'''
CLOUD = "CLOUD"
DATABASE_URL = "DATABASE_URL"
POSTGRES_SQL = "postgres://"
POSTGRES_SQL_DEPLOYED = "postgresql://"

'''
Dashboard Values
'''
DASHBOARD_DEFAULT_NAME = "dashboard"


'''
Roadmap Values
'''
ROADMAP_DEFAULT_NAME = "roadmap"

MAJOR_SPECIFIC_FOLDER_NAME = "majorSpecific/"

ECON_DEFAULT_NAME = "econ"
CS_DEFAULT_NAME = "cs"

'''
Landing Values
'''
LANDING_DEFAULT_NAME = "landing"

'''
HTTP constants
'''
class HTTPMethod:
    GET    = "GET"
    POST   = "POST"
    PUT    = "PUT"
    PATCH  = "PATCH"
    DELETE = "DELETE"


class HTTPStatus:
    OK                    = 200
    CREATED               = 201
    NO_CONTENT            = 204
    BAD_REQUEST           = 400
    UNAUTHORIZED          = 401
    FORBIDDEN             = 403
    NOT_FOUND             = 404
    CONFLICT              = 409
    UNPROCESSABLE_ENTITY  = 422
    INTERNAL_SERVER_ERROR = 500

'''
misc
'''
PREFIX = "/"
HTML_EXTENSION = ".html"


