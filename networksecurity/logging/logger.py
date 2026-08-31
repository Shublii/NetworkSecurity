##Logging = recording what is happening inside your project.
##Why use logging?

#Helps find errors
#Shows which step is running
#Makes debugging easier
#Keeps a record of project execution
#Very useful when the project is deployed





# import logging
# import os
# from datetime import datetime

# LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%M_%S')}.log"

# # logger.py
# # __file__ = networksecurity/logging/logger.py
# #
# # Go up from logging -> networksecurity
# networksecurity_path = os.path.dirname(os.path.dirname(__file__))

# # Then go into exception/logs
# logs_path = os.path.join(networksecurity_path, "exception", "logs")

# os.makedirs(logs_path, exist_ok=True)

# LOG_FILE_PATH = os.path.join(logs_path, LOG_FILE)

# logging.basicConfig(
#     filename=LOG_FILE_PATH,
#     format="[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s",
#     level=logging.INFO
# )














##Udmy

# import logging
# import os
# from datetime import datetime

# LOG_FILE=f"{datetime.now().strftime('%m_%d_%Y_%M_%S')}.log"

# logs_path = os.path.join(os.getcwd(), "logs", LOG_FILE)

# os.makedirs(logs_path, exist_ok=True)
# LOG_FILE_PATH = os.path.join(logs_path, LOG_FILE)

# logging.basicConfig(
#     filename=LOG_FILE_PATH,
#     format="[%(asctime)s] %(lineno)d %(name)s - %(levelname)s - %(message)s",
#     level=logging.INFO,
# )



import logging
import os
from datetime import datetime
 
LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
 
logs_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(logs_dir, exist_ok=True)
 
LOG_FILE_PATH = os.path.join(logs_dir, LOG_FILE)
 
logging.basicConfig(
    filename=LOG_FILE_PATH,
    format="[%(asctime)s] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
