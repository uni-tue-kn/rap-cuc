import logging 

class Logger:
    def __init__(self, module_name):
        logging.basicConfig(
                filename= module_name, 
                level=logging.INFO,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filemode='w')

        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        self.logger = logging.getLogger(module_name)
        self.logger.addHandler(ch)
        

    def get_logger(self):
        return self.logger
