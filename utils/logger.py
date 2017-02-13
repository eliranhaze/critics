import logging
from logging.handlers import TimedRotatingFileHandler

formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
handler = TimedRotatingFileHandler('log/critics.log', when='midnight', backupCount=10) 
handler.setFormatter(formatter)

def get_logger(name):
    logger = logging.getLogger(name)
    logger.addHandler(handler)          
    logger.setLevel(logging.DEBUG)
    return logger
