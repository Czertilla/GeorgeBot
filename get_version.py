def get_version():
    try:
        with open(".git/COMMIT_EDITMSG") as f:
            version = f.readline().replace('\n', '')
    except:
        version = "unknow_ver"
    finally:
        return version