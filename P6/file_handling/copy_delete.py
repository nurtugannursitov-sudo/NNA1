import shutil
import os

shutil.copy2("file.txt", "file_backup.txt")


import os
if os.path.exists("file.txt"):
  os.remove("file.txt")