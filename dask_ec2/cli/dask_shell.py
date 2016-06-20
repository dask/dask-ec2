import os
from distributed import Executor

e = Executor(os.environ["DISTRIBUTED_ADDRESS"])

print("Dask.Distributed executor is available as `e`")
