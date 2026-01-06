import os
import time
import requests

def clear():
    os.system("clear")

def check_online(place_id):
    try:
        url = f"https://games.roblox.com/v1/games?universeIds={place_id}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return len(r.json()["data"]) > 0
    except:
        pass
    return False

def open_roblox(link):
    os.system(f'am start "{link}"')

def join_normal():
    place_id = input("Nhập PlaceId: ").strip()
    job_id = input("Nhập JobId (Enter để random server): ").strip()

    if not place_id.isdigit():
        print("❌ PlaceId không hợp lệ")
        return

    print("⏳ Checking server...")
    if not check_online(place_id):
        print("🔴 Server OFFLINE")
        return

    print("🟢 Server ONLINE")

    if job_id:
        link = f"roblox://placeId={place_id}&gameInstanceId={job_id}"
    else:
        link = f"roblox://placeId={place_id}"

    open_roblox(link)

def join_vip():
    vip = input("Nhập VIP Server Link: ").strip()
    if "roblox.com" not in vip:
        print("❌ Link không hợp lệ")
        return
    open_roblox(vip)

def auto_rejoin():
    place_id = input("Nhập PlaceId: ").strip()
    delay = input("Delay (giây, mặc định 10): ").strip()
    delay = int(delay) if delay.isdigit() else 10

    print("🔁 Auto Rejoin đang chạy... Ctrl+C để dừng")

    while True:
        if check_online(place_id):
            open_roblox(f"roblox://placeId={place_id}")
            time.sleep(delay)
        else:
            print("🔴 Server OFFLINE, chờ...")
            time.sleep(5)

def menu():
    while True:
        clear()
        print("===== ROBLOX REJOIN TOOL (TERMUX) =====")
        print("1. Join server (PlaceId / JobId)")
        print("2. Join VIP server (Link)")
        print("3. Auto Rejoin + Check Online")
        print("0. Thoát")
        print("=====================================")

        choice = input("Chọn: ").strip()

        if choice == "1":
            join_normal()
        elif choice == "2":
            join_vip()
        elif choice == "3":
            auto_rejoin()
        elif choice == "0":
            break
        else:
            print("❌ Lựa chọn không hợp lệ")

        input("\nNhấn Enter để tiếp tục...")

if __name__ == "__main__":
    menu()

