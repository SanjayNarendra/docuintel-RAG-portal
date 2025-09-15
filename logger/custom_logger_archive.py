import os
import logging
from datetime import datetime

# class CustomLogger:
#     def __init__(self, log_dir="logs"):
#         # Ensure logs directory exists
#         self.logs_dir = os.path.join(os.getcwd(), log_dir)
#         os.makedirs(self.logs_dir, exist_ok=True)

#         # Timestamped log file name 
#         log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
#         log_file_path = os.path.join(self.logs_dir, log_file)
        
#         # Configure logging
#         logging.basicConfig(
#             filename = log_file_path,
#             format="[ %(asctime)s ] %(levelname)s %(name)s (line:%(lineno)d) - %(message)s",
#             level=logging.INFO,
#         )

#     def get_logger(self, name=__file__):
#         return logging.getLogger(os.path.basename(name)) 
    
  
# #if __name__ == "__main__":
# #    logger = CustomLogger()
# #    logger = logger.get_logger(__file__)
# #    logger.info("Custom logger initialized")


## stream handler class 
class CustomLogger: 
    def __init__(self, log_dir="logs"): 
        # Ensure logs directory exists
        self.logs_dir = os.path.join(os.getcwd(), log_dir)
        os.makedirs(self.logs_dir, exist_ok=True)

        # Timestamped log file name 
        log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
        self.log_file_path = os.path.join(self.logs_dir, log_file)

    def get_logger(self, name=__file__):
        """
        Returns a logger instance with both file and stream (console) handlers.
        Default name is the current file name.
        """
        logger_name = os.path.basename(name)
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        # Formatter for the handlers
        file_formatter = logging.Formatter(
            "[ %(asctime)s ] %(levelname)s %(name)s (line:%(lineno)d) - %(message)s"
            )
        
        console_formatter = logging.Formatter(
            "%(levelname)s - %(message)s"
            )
        
        # File handler
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)

        # Avoid adding multiple handlers to the logger
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger
        

# --- Example usage --- 
if __name__ == "__main__":
    logger = CustomLogger()
    logger = logger.get_logger(__file__)
    logger.info("logger with stream handler initialized")

