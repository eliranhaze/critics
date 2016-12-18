from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

class Executor(object):

    def __init__(self, num_workers=12):
        self.pool = ThreadPoolExecutor(num_workers)

    def execute(self, task, arg_list, timeout):
        futures = [
            self.pool.submit(task, arg)
            for arg in arg_list
        ]
        futures = wait(futures, timeout, return_when = ALL_COMPLETED)
        for future in futures.not_done:
            future.cancel()
        results = [future.result() for future in futures.done]
        return [result for result in results if result is not None]
