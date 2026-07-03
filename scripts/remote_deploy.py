"""
远程部署脚本 - 通过 paramiko SSH 连接服务器执行 git pull + docker build + docker run
"""
import paramiko
import sys
import time

HOST = "jiiii.cn"
PORT = 22
USER = "root"
PASSWORD = "123456
PROJECT_DIR = "/tmp/card"
CONTAINER_NAME = "card-game"
HOST_PORT = 28888
CONTAINER_PORT = 8000


def safe_print(text):
    """Windows GBK 安全打印"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("gbk", errors="replace").decode("gbk"))


def run_command(ssh, cmd, desc=""):
    if desc:
        safe_print(f"\n{'='*50}")
        safe_print(f"  {desc}")
        safe_print(f"{'='*50}")
    safe_print(f"$ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=300)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out:
        for line in out.split("\n"):
            safe_print(f"  {line}")
    if err and exit_code != 0:
        for line in err.split("\n"):
            safe_print(f"  [ERR] {line}")
    if exit_code != 0:
        safe_print(f"  [FAIL] exit code: {exit_code}")
        return False
    safe_print(f"  [OK]")
    return True


def main():
    safe_print(f"Connecting to {HOST}:{PORT} ...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    except Exception as e:
        safe_print(f"SSH connection failed: {e}")
        sys.exit(1)

    safe_print("Connected!\n")

    steps = [
        ("docker kill $(docker ps -q) 2>/dev/null; docker builder prune -f 2>/dev/null; echo 'cleanup done'", "0/5 - Kill Stuck Builds & Cleanup"),
        (f"cd {PROJECT_DIR} && git checkout -- . && git pull origin master", "1/5 - Git Pull"),
        (f"cd {PROJECT_DIR} && docker stop {CONTAINER_NAME} 2>/dev/null; docker rm {CONTAINER_NAME} 2>/dev/null; echo 'old container cleaned'", "2/5 - Stop & Remove Old Container"),
        (f"cd {PROJECT_DIR} && docker build -t {CONTAINER_NAME} .", "3/5 - Docker Build"),
        (f"docker run -d --name {CONTAINER_NAME} -p {HOST_PORT}:{CONTAINER_PORT} -v card_game_data:/app/data -v card_game_images:/app/backend/static/images --restart unless-stopped {CONTAINER_NAME}", "4/5 - Docker Run"),
        (f"sleep 3 && docker ps --filter name={CONTAINER_NAME} --format 'table {{{{.Names}}}}\t{{{{.Status}}}}\t{{{{.Ports}}}}'", "5/5 - Verify"),
    ]

    success = True
    for cmd, desc in steps:
        if not run_command(ssh, cmd, desc):
            success = False
            break

    ssh.close()

    if success:
        safe_print(f"\nDeploy SUCCESS! Game running at http://{HOST}:{HOST_PORT}")
    else:
        safe_print(f"\nDeploy FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
