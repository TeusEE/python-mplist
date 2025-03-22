import multiprocessing as mp
from threading import Lock

def worker(q, idx, ret_dict):
    dts = {}
    while True:
        ctx = q.get()
        if ctx["tk"] == "create":
            dts[ctx["keys"]] = [i for i in range(idx*ctx["val"], (idx+1)*ctx["val"])]
            ret_dict[idx] = dts


        elif ctx["tk"] == "print":
            print(ret_dict[idx][ctx["keys"]])


        if ctx["tk"] == "stop":
            break


class proc_mgr:
    _instance = None
    _lock = Lock()  # To ensure thread safety for singleton creation

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(proc_mgr, cls).__new__(cls)
        return cls._instance

    def __init__(self, proc_cnt=2):
        if not hasattr(self, "initialized"):  # Prevent reinitialization
            self.proc_cnt = proc_cnt
            self.manager = mp.Manager()
            self.ret_dict = self.manager.dict()
            self.qs = [mp.Queue() for _ in range(self.proc_cnt)]
            self.proces = [
                mp.Process(target=worker, args=(self.qs[idx], idx, self.ret_dict))
                for idx in range(self.proc_cnt)
            ]
            for p in self.proces:
                p.start()
            self.initialized = True

    def stop_all(self):
        for q in self.qs:
            q.put({"tk": "stop"})
        for p in self.proces:
            p.join()

class ind_list:
    _proc_mgr = None
    _keys = []
    dt_index = 0

    @classmethod
    def init_proc(cls):
        if cls._proc_mgr is None:
            cls._proc_mgr = proc_mgr()

    def __init__(self, key):
        self.key = key

    def create(self, val):
        self._keys.append(self.dt_index)
        [q.put({"tk": "create", "keys": self.dt_index, "val": int(val / self._proc_mgr.proc_cnt)}) for q in self._proc_mgr.qs]
        try:
            return self.dt_index
        finally:
            self.dt_index = self.dt_index + 1

    def add(self, target_comp):
        [q.put({"tk": "add", "keys": target_comp.key}) for q in self._proc_mgr.qs]

    def print(self, key):
        [q.put({"tk": "print", "keys": key}) for q in self._proc_mgr.qs]


if __name__ == "__main__":
    # 반드시 __name__ == "__main__" 블록에서만 ind_list를 사용
    ind_list.init_proc()
    mylist1 = ind_list(0)
    mylist2 = ind_list(1)
    
    mylist1.create(100000)
    mylist2.create(100000)
    ind_list._proc_mgr.stop_all()
